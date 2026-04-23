def train_uvf(train_dir,
              environment=None,
              num_bin_actions=3,
              agent_class=None,
              meta_agent_class=None,
              state_preprocess_class=None,
              inverse_dynamics_class=None,
              exp_action_wrapper=None,
              replay_buffer=None,
              meta_replay_buffer=None,
              replay_num_steps=1,
              meta_replay_num_steps=1,
              critic_optimizer=None,
              actor_optimizer=None,
              meta_critic_optimizer=None,
              meta_actor_optimizer=None,
              repr_optimizer=None,
              relabel_contexts=False,
              meta_relabel_contexts=False,
              batch_size=64,
              repeat_size=0,
              num_episodes_train=2000,
              initial_episodes=2,
              initial_steps=None,
              num_updates_per_observation=1,
              num_collect_per_update=1,
              num_collect_per_meta_update=1,
              gamma=1.0,
              meta_gamma=1.0,
              reward_scale_factor=1.0,
              target_update_period=1,
              should_stop_early=None,
              clip_gradient_norm=0.0,
              summarize_gradients=False,
              debug_summaries=False,
              log_every_n_steps=100,
              prefetch_queue_capacity=2,
              policy_save_dir='policy',
              save_policy_every_n_steps=1000,
              save_policy_interval_secs=0,
              replay_context_ratio=0.0,
              next_state_as_context_ratio=0.0,
              state_index=0,
              zero_timer_ratio=0.0,
              timer_index=-1,
              debug=False,
              max_policies_to_save=None,
              max_steps_per_episode=None,
              load_path=LOAD_PATH):
  """Train an agent."""
  tf_env = create_maze_env.TFPyEnvironment(environment)
  observation_spec = [tf_env.observation_spec()]
  action_spec = [tf_env.action_spec()]

  max_steps_per_episode = max_steps_per_episode or tf_env.pyenv.max_episode_steps

  assert max_steps_per_episode, 'max_steps_per_episode need to be set'

  if initial_steps is None:
    initial_steps = initial_episodes * max_steps_per_episode

  if agent_class.ACTION_TYPE == 'discrete':
    assert False
  else:
    assert agent_class.ACTION_TYPE == 'continuous'

  assert agent_class.ACTION_TYPE == meta_agent_class.ACTION_TYPE
  with tf.variable_scope('meta_agent'):
    meta_agent = meta_agent_class(
        observation_spec,
        action_spec,
        tf_env,
        debug_summaries=debug_summaries)
  meta_agent.set_replay(replay=meta_replay_buffer)

  with tf.variable_scope('uvf_agent'):
    uvf_agent = agent_class(
        observation_spec,
        action_spec,
        tf_env,
        debug_summaries=debug_summaries)
    uvf_agent.set_meta_agent(agent=meta_agent)
    uvf_agent.set_replay(replay=replay_buffer)

  with tf.variable_scope('state_preprocess'):
    state_preprocess = state_preprocess_class()

  with tf.variable_scope('inverse_dynamics'):
    inverse_dynamics = inverse_dynamics_class(
        meta_agent.sub_context_as_action_specs[0])

  # Create counter variables
  global_step = tf.contrib.framework.get_or_create_global_step()
  num_episodes = tf.Variable(0, dtype=tf.int64, name='num_episodes')
  num_resets = tf.Variable(0, dtype=tf.int64, name='num_resets')
  num_updates = tf.Variable(0, dtype=tf.int64, name='num_updates')
  num_meta_updates = tf.Variable(0, dtype=tf.int64, name='num_meta_updates')
  episode_rewards = tf.Variable([0.] * 100, name='episode_rewards')
  episode_meta_rewards = tf.Variable([0.] * 100, name='episode_meta_rewards')

  # Create counter variables summaries
  train_utils.create_counter_summaries([
      ('environment_steps', global_step),
      ('num_episodes', num_episodes),
      ('num_resets', num_resets),
      ('num_updates', num_updates),
      ('num_meta_updates', num_meta_updates),
      ('replay_buffer_adds', replay_buffer.get_num_adds()),
      ('meta_replay_buffer_adds', meta_replay_buffer.get_num_adds()),
  ])

  tf.summary.scalar('avg_episode_rewards',
                    tf.reduce_mean(episode_rewards[1:]))
  tf.summary.scalar('avg_episode_meta_rewards',
                    tf.reduce_mean(episode_meta_rewards[1:]))
  tf.summary.histogram('episode_rewards', episode_rewards[1:])
  tf.summary.histogram('episode_meta_rewards', episode_meta_rewards[1:])

  # Create init ops
  action_fn = uvf_agent.action
  action_fn = uvf_agent.add_noise_fn(action_fn, global_step=None)
  meta_action_fn = meta_agent.action
  meta_action_fn = meta_agent.add_noise_fn(meta_action_fn, global_step=None)
  meta_actions_fn = meta_agent.actions
  meta_actions_fn = meta_agent.add_noise_fn(meta_actions_fn, global_step=None)
  init_collect_experience_op = collect_experience(
      tf_env,
      uvf_agent,
      meta_agent,
      state_preprocess,
      replay_buffer,
      meta_replay_buffer,
      action_fn,
      meta_action_fn,
      environment_steps=global_step,
      num_episodes=num_episodes,
      num_resets=num_resets,
      episode_rewards=episode_rewards,
      episode_meta_rewards=episode_meta_rewards,
      store_context=True,
      disable_agent_reset=False,
  )

  # Create train ops
  collect_experience_op = collect_experience(
      tf_env,
      uvf_agent,
      meta_agent,
      state_preprocess,
      replay_buffer,
      meta_replay_buffer,
      action_fn,
      meta_action_fn,
      environment_steps=global_step,
      num_episodes=num_episodes,
      num_resets=num_resets,
      episode_rewards=episode_rewards,
      episode_meta_rewards=episode_meta_rewards,
      store_context=True,
      disable_agent_reset=False,
  )

  train_op_list = []
  repr_train_op = tf.constant(0.0)
  for mode in ['meta', 'nometa']:
    if mode == 'meta':
      agent = meta_agent
      buff = meta_replay_buffer
      critic_opt = meta_critic_optimizer
      actor_opt = meta_actor_optimizer
      relabel = meta_relabel_contexts
      num_steps = meta_replay_num_steps
      my_gamma = meta_gamma,
      n_updates = num_meta_updates
    else:
      agent = uvf_agent
      buff = replay_buffer
      critic_opt = critic_optimizer
      actor_opt = actor_optimizer
      relabel = relabel_contexts
      num_steps = replay_num_steps
      my_gamma = gamma
      n_updates = num_updates

    with tf.name_scope(mode):
      batch = buff.get_random_batch(batch_size, num_steps=num_steps)
      states, actions, rewards, discounts, next_states = batch[:5]
      with tf.name_scope('Reward'):
        tf.summary.scalar('average_step_reward', tf.reduce_mean(rewards))
      rewards *= reward_scale_factor
      batch_queue = slim.prefetch_queue.prefetch_queue(
          [states, actions, rewards, discounts, next_states] + batch[5:],
          capacity=prefetch_queue_capacity,
          name='batch_queue')

      batch_dequeue = batch_queue.dequeue()
      if repeat_size > 0:
        batch_dequeue = [
            tf.tile(batch, (repeat_size+1,) + (1,) * (batch.shape.ndims - 1))
            for batch in batch_dequeue
        ]
        batch_size *= (repeat_size + 1)
      states, actions, rewards, discounts, next_states = batch_dequeue[:5]
      if mode == 'meta':
        low_states = batch_dequeue[5]
        low_actions = batch_dequeue[6]
        low_state_reprs = state_preprocess(low_states)
      state_reprs = state_preprocess(states)
      next_state_reprs = state_preprocess(next_states)

      if mode == 'meta':  # Re-label meta-action
        prev_actions = actions
        if FLAGS.goal_sample_strategy == 'None':
          pass
        elif FLAGS.goal_sample_strategy == 'FuN':
          actions = inverse_dynamics.sample(state_reprs, next_state_reprs, 1, prev_actions, sc=0.1)
          actions = tf.stop_gradient(actions)
        elif FLAGS.goal_sample_strategy == 'sample':
          actions = sample_best_meta_actions(state_reprs, next_state_reprs, prev_actions,
                                             low_states, low_actions, low_state_reprs,
                                             inverse_dynamics, uvf_agent, k=10)
        else:
          assert False

      if state_preprocess.trainable and mode == 'meta':
        # Representation learning is based on meta-transitions, but is trained
        # along with low-level policy updates.
        repr_loss, _, _ = state_preprocess.loss(states, next_states, low_actions, low_states)
        repr_train_op = slim.learning.create_train_op(
            repr_loss,
            repr_optimizer,
            global_step=None,
            update_ops=None,
            summarize_gradients=summarize_gradients,
            clip_gradient_norm=clip_gradient_norm,
            variables_to_train=state_preprocess.get_trainable_vars(),)

      # Get contexts for training
      contexts, next_contexts = agent.sample_contexts(
          mode='train', batch_size=batch_size,
          state=states, next_state=next_states,
      )
      if not relabel:  # Re-label context (in the style of TDM or HER).
        contexts, next_contexts = (
            batch_dequeue[-2*len(contexts):-1*len(contexts)],
            batch_dequeue[-1*len(contexts):])

      merged_states = agent.merged_states(states, contexts)
      merged_next_states = agent.merged_states(next_states, next_contexts)
      if mode == 'nometa':
        context_rewards, context_discounts = agent.compute_rewards(
            'train', state_reprs, actions, rewards, next_state_reprs, contexts)
      elif mode == 'meta': # Meta-agent uses sum of rewards, not context-specific rewards.
        _, context_discounts = agent.compute_rewards(
            'train', states, actions, rewards, next_states, contexts)
        context_rewards = rewards

      if agent.gamma_index is not None:
        context_discounts *= tf.cast(
            tf.reshape(contexts[agent.gamma_index], (-1,)),
            dtype=context_discounts.dtype)
      else: context_discounts *= my_gamma

      critic_loss = agent.critic_loss(merged_states, actions,
                                      context_rewards, context_discounts,
                                      merged_next_states)

      critic_loss = tf.reduce_mean(critic_loss)

      actor_loss = agent.actor_loss(merged_states, actions,
                                    context_rewards, context_discounts,
                                    merged_next_states)
      actor_loss *= tf.to_float(  # Only update actor every N steps.
          tf.equal(n_updates % target_update_period, 0))

      critic_train_op = slim.learning.create_train_op(
          critic_loss,
          critic_opt,
          global_step=n_updates,
          update_ops=None,
          summarize_gradients=summarize_gradients,
          clip_gradient_norm=clip_gradient_norm,
          variables_to_train=agent.get_trainable_critic_vars(),)
      critic_train_op = uvf_utils.tf_print(
          critic_train_op, [critic_train_op],
          message='critic_loss',
          print_freq=1000,
          name='critic_loss')
      train_op_list.append(critic_train_op)
      if actor_loss is not None:
        actor_train_op = slim.learning.create_train_op(
            actor_loss,
            actor_opt,
            global_step=None,
            update_ops=None,
            summarize_gradients=summarize_gradients,
            clip_gradient_norm=clip_gradient_norm,
            variables_to_train=agent.get_trainable_actor_vars(),)
        actor_train_op = uvf_utils.tf_print(
            actor_train_op, [actor_train_op],
            message='actor_loss',
            print_freq=1000,
            name='actor_loss')
        train_op_list.append(actor_train_op)

  assert len(train_op_list) == 4
  # Update targets should happen after the networks have been updated.
  with tf.control_dependencies(train_op_list[2:]):
    update_targets_op = uvf_utils.periodically(
        uvf_agent.update_targets, target_update_period, 'update_targets')
  if meta_agent is not None:
    with tf.control_dependencies(train_op_list[:2]):
      update_meta_targets_op = uvf_utils.periodically(
          meta_agent.update_targets, target_update_period, 'update_targets')

  assert_op = tf.Assert(  # Hack to get training to stop.
      tf.less_equal(global_step, 200 + num_episodes_train * max_steps_per_episode),
      [global_step])
  with tf.control_dependencies([update_targets_op, assert_op]):
    train_op = tf.add_n(train_op_list[2:], name='post_update_targets')
    # Representation training steps on every low-level policy training step.
    train_op += repr_train_op
  with tf.control_dependencies([update_meta_targets_op, assert_op]):
    meta_train_op = tf.add_n(train_op_list[:2],
                             name='post_update_meta_targets')

  if debug_summaries:
    train_.gen_debug_batch_summaries(batch)
    slim.summaries.add_histogram_summaries(
        uvf_agent.get_trainable_critic_vars(), 'critic_vars')
    slim.summaries.add_histogram_summaries(
        uvf_agent.get_trainable_actor_vars(), 'actor_vars')

  train_ops = train_utils.TrainOps(train_op, meta_train_op,
                                   collect_experience_op)

  policy_save_path = os.path.join(train_dir, policy_save_dir, 'model.ckpt')
  policy_vars = uvf_agent.get_actor_vars() + meta_agent.get_actor_vars() + [
      global_step, num_episodes, num_resets
  ] + list(uvf_agent.context_vars) + list(meta_agent.context_vars) + state_preprocess.get_trainable_vars()
  # add critic vars, since some test evaluation depends on them
  policy_vars += uvf_agent.get_trainable_critic_vars() + meta_agent.get_trainable_critic_vars()
  policy_saver = tf.train.Saver(
      policy_vars, max_to_keep=max_policies_to_save, sharded=False)

  lowlevel_vars = (uvf_agent.get_actor_vars() +
                   uvf_agent.get_trainable_critic_vars() +
                   state_preprocess.get_trainable_vars())
  lowlevel_saver = tf.train.Saver(lowlevel_vars)

  def policy_save_fn(sess):
    policy_saver.save(
        sess, policy_save_path, global_step=global_step, write_meta_graph=False)
    if save_policy_interval_secs > 0:
      tf.logging.info(
          'Wait %d secs after save policy.' % save_policy_interval_secs)
      time.sleep(save_policy_interval_secs)

  train_step_fn = train_utils.TrainStep(
      max_number_of_steps=num_episodes_train * max_steps_per_episode + 100,
      num_updates_per_observation=num_updates_per_observation,
      num_collect_per_update=num_collect_per_update,
      num_collect_per_meta_update=num_collect_per_meta_update,
      log_every_n_steps=log_every_n_steps,
      policy_save_fn=policy_save_fn,
      save_policy_every_n_steps=save_policy_every_n_steps,
      should_stop_early=should_stop_early).train_step

  local_init_op = tf.local_variables_initializer()
  init_targets_op = tf.group(uvf_agent.update_targets(1.0),
                             meta_agent.update_targets(1.0))

  def initialize_training_fn(sess):
    """Initialize training function."""
    sess.run(local_init_op)
    sess.run(init_targets_op)
    if load_path:
      tf.logging.info('Restoring low-level from %s' % load_path)
      lowlevel_saver.restore(sess, load_path)
    global_step_value = sess.run(global_step)
    assert global_step_value == 0, 'Global step should be zero.'
    collect_experience_call = sess.make_callable(
        init_collect_experience_op)

    for _ in range(initial_steps):
      collect_experience_call()

  train_saver = tf.train.Saver(max_to_keep=2, sharded=True)
  tf.logging.info('train dir: %s', train_dir)
  return slim.learning.train(
      train_ops,
      train_dir,
      train_step_fn=train_step_fn,
      save_interval_secs=FLAGS.save_interval_secs,
      saver=train_saver,
      log_every_n_steps=0,
      global_step=global_step,
      master="",
      is_chief=(FLAGS.task == 0),
      save_summaries_secs=FLAGS.save_summaries_secs,
      init_fn=initialize_training_fn)