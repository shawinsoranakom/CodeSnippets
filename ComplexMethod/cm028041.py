def collect_experience(tf_env, agent, meta_agent, state_preprocess,
                       replay_buffer, meta_replay_buffer,
                       action_fn, meta_action_fn,
                       environment_steps, num_episodes, num_resets,
                       episode_rewards, episode_meta_rewards,
                       store_context,
                       disable_agent_reset):
  """Collect experience in a tf_env into a replay_buffer using action_fn.

  Args:
    tf_env: A TFEnvironment.
    agent: A UVF agent.
    meta_agent: A Meta Agent.
    replay_buffer: A Replay buffer to collect experience in.
    meta_replay_buffer: A Replay buffer to collect meta agent experience in.
    action_fn: A function to produce actions given current state.
    meta_action_fn: A function to produce meta actions given current state.
    environment_steps: A variable to count the number of steps in the tf_env.
    num_episodes: A variable to count the number of episodes.
    num_resets: A variable to count the number of resets.
    store_context: A boolean to check if store context in replay.
    disable_agent_reset: A boolean that disables agent from resetting.

  Returns:
    A collect_experience_op that excute an action and store into the
    replay_buffers
  """
  tf_env.start_collect()
  state = tf_env.current_obs()
  state_repr = state_preprocess(state)
  action = action_fn(state, context=None)

  with tf.control_dependencies([state]):
    transition_type, reward, discount = tf_env.step(action)

  def increment_step():
    return environment_steps.assign_add(1)

  def increment_episode():
    return num_episodes.assign_add(1)

  def increment_reset():
    return num_resets.assign_add(1)

  def update_episode_rewards(context_reward, meta_reward, reset):
    new_episode_rewards = tf.concat(
        [episode_rewards[:1] + context_reward, episode_rewards[1:]], 0)
    new_episode_meta_rewards = tf.concat(
        [episode_meta_rewards[:1] + meta_reward,
         episode_meta_rewards[1:]], 0)
    return tf.group(
        episode_rewards.assign(
            tf.cond(reset,
                    lambda: tf.concat([[0.], episode_rewards[:-1]], 0),
                    lambda: new_episode_rewards)),
        episode_meta_rewards.assign(
            tf.cond(reset,
                    lambda: tf.concat([[0.], episode_meta_rewards[:-1]], 0),
                    lambda: new_episode_meta_rewards)))

  def no_op_int():
    return tf.constant(0, dtype=tf.int64)

  step_cond = agent.step_cond_fn(state, action,
                                 transition_type,
                                 environment_steps, num_episodes)
  reset_episode_cond = agent.reset_episode_cond_fn(
      state, action,
      transition_type, environment_steps, num_episodes)
  reset_env_cond = agent.reset_env_cond_fn(state, action,
                                           transition_type,
                                           environment_steps, num_episodes)

  increment_step_op = tf.cond(step_cond, increment_step, no_op_int)
  increment_episode_op = tf.cond(reset_episode_cond, increment_episode,
                                 no_op_int)
  increment_reset_op = tf.cond(reset_env_cond, increment_reset, no_op_int)
  increment_op = tf.group(increment_step_op, increment_episode_op,
                          increment_reset_op)

  with tf.control_dependencies([increment_op, reward, discount]):
    next_state = tf_env.current_obs()
    next_state_repr = state_preprocess(next_state)
    next_reset_episode_cond = tf.logical_or(
        agent.reset_episode_cond_fn(
            state, action,
            transition_type, environment_steps, num_episodes),
        tf.equal(discount, 0.0))

  if store_context:
    context = [tf.identity(var) + tf.zeros_like(var) for var in agent.context_vars]
    meta_context = [tf.identity(var) + tf.zeros_like(var) for var in meta_agent.context_vars]
  else:
    context = []
    meta_context = []
  with tf.control_dependencies([next_state] + context + meta_context):
    if disable_agent_reset:
      collect_experience_ops = [tf.no_op()]  # don't reset agent
    else:
      collect_experience_ops = agent.cond_begin_episode_op(
          tf.logical_not(reset_episode_cond),
          [state, action, reward, next_state,
           state_repr, next_state_repr],
          mode='explore', meta_action_fn=meta_action_fn)
      context_reward, meta_reward = collect_experience_ops
      collect_experience_ops = list(collect_experience_ops)
      collect_experience_ops.append(
          update_episode_rewards(tf.reduce_sum(context_reward), meta_reward,
                                 reset_episode_cond))

  meta_action_every_n = agent.tf_context.meta_action_every_n
  with tf.control_dependencies(collect_experience_ops):
    transition = [state, action, reward, discount, next_state]

    meta_action = tf.to_float(
        tf.concat(context, -1))  # Meta agent action is low-level context

    meta_end = tf.logical_and(  # End of meta-transition.
        tf.equal(agent.tf_context.t % meta_action_every_n, 1),
        agent.tf_context.t > 1)
    with tf.variable_scope(tf.get_variable_scope(), reuse=tf.AUTO_REUSE):
      states_var = tf.get_variable('states_var',
                                   [meta_action_every_n, state.shape[-1]],
                                   state.dtype)
      actions_var = tf.get_variable('actions_var',
                                    [meta_action_every_n, action.shape[-1]],
                                    action.dtype)
      state_var = tf.get_variable('state_var', state.shape, state.dtype)
      reward_var = tf.get_variable('reward_var', reward.shape, reward.dtype)
      meta_action_var = tf.get_variable('meta_action_var',
                                        meta_action.shape, meta_action.dtype)
      meta_context_var = [
          tf.get_variable('meta_context_var%d' % idx,
                          meta_context[idx].shape, meta_context[idx].dtype)
          for idx in range(len(meta_context))]

    actions_var_upd = tf.scatter_update(
        actions_var, (agent.tf_context.t - 2) % meta_action_every_n, action)
    with tf.control_dependencies([actions_var_upd]):
      actions = tf.identity(actions_var) + tf.zeros_like(actions_var)
      meta_reward = tf.identity(meta_reward) + tf.zeros_like(meta_reward)
      meta_reward = tf.reshape(meta_reward, reward.shape)

    reward = 0.1 * meta_reward
    meta_transition = [state_var, meta_action_var,
                       reward_var + reward,
                       discount * (1 - tf.to_float(next_reset_episode_cond)),
                       next_state]
    meta_transition.extend([states_var, actions])
    if store_context:  # store current and next context into replay
      transition += context + list(agent.context_vars)
      meta_transition += meta_context_var + list(meta_agent.context_vars)

    meta_step_cond = tf.squeeze(tf.logical_and(step_cond, tf.logical_or(next_reset_episode_cond, meta_end)))

    collect_experience_op = tf.group(
        replay_buffer.maybe_add(transition, step_cond),
        meta_replay_buffer.maybe_add(meta_transition, meta_step_cond),
    )

  with tf.control_dependencies([collect_experience_op]):
    collect_experience_op = tf.cond(reset_env_cond,
                                    tf_env.reset,
                                    tf_env.current_time_step)

    meta_period = tf.equal(agent.tf_context.t % meta_action_every_n, 1)
    states_var_upd = tf.scatter_update(
        states_var, (agent.tf_context.t - 1) % meta_action_every_n,
        next_state)
    state_var_upd = tf.assign(
        state_var,
        tf.cond(meta_period, lambda: next_state, lambda: state_var))
    reward_var_upd = tf.assign(
        reward_var,
        tf.cond(meta_period,
                lambda: tf.zeros_like(reward_var),
                lambda: reward_var + reward))
    meta_action = tf.to_float(tf.concat(agent.context_vars, -1))
    meta_action_var_upd = tf.assign(
        meta_action_var,
        tf.cond(meta_period, lambda: meta_action, lambda: meta_action_var))
    meta_context_var_upd = [
        tf.assign(
            meta_context_var[idx],
            tf.cond(meta_period,
                    lambda: meta_agent.context_vars[idx],
                    lambda: meta_context_var[idx]))
        for idx in range(len(meta_context))]

  return tf.group(
      collect_experience_op,
      states_var_upd,
      state_var_upd,
      reward_var_upd,
      meta_action_var_upd,
      *meta_context_var_upd)