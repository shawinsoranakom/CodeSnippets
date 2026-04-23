def evaluate(checkpoint_dir,
             eval_dir,
             environment=None,
             num_bin_actions=3,
             agent_class=None,
             meta_agent_class=None,
             state_preprocess_class=None,
             gamma=1.0,
             num_episodes_eval=10,
             eval_interval_secs=60,
             max_number_of_evaluations=None,
             checkpoint_timeout=None,
             timeout_fn=None,
             tuner_hook=None,
             generate_videos=False,
             generate_summaries=True,
             num_episodes_videos=5,
             video_settings=None,
             eval_modes=('eval',),
             eval_model_rollout=False,
             policy_save_dir='policy',
             checkpoint_range=None,
             checkpoint_path=None,
             max_steps_per_episode=None,
             evaluate_nohrl=False):
  """Loads and repeatedly evaluates a checkpointed model at a set interval.

  Args:
    checkpoint_dir: The directory where the checkpoints reside.
    eval_dir: Directory to save the evaluation summary results.
    environment: A BaseEnvironment to evaluate.
    num_bin_actions: Number of bins for discretizing continuous actions.
    agent_class: An RL agent class.
    meta_agent_class: A Meta agent class.
    gamma: Discount factor for the reward.
    num_episodes_eval: Number of episodes to evaluate and average reward over.
    eval_interval_secs: The number of seconds between each evaluation run.
    max_number_of_evaluations: The max number of evaluations. If None the
      evaluation continues indefinitely.
    checkpoint_timeout: The maximum amount of time to wait between checkpoints.
      If left as `None`, then the process will wait indefinitely.
    timeout_fn: Optional function to call after a timeout.
    tuner_hook: A callable that takes the average reward and global step and
      updates a Vizier tuner trial.
    generate_videos: Whether to generate videos of the agent in action.
    generate_summaries: Whether to generate summaries.
    num_episodes_videos: Number of episodes to evaluate for generating videos.
    video_settings: Settings for generating videos of the agent.
      optimal action based on the critic.
    eval_modes: A tuple of eval modes.
    eval_model_rollout: Evaluate model rollout.
    policy_save_dir: Optional sub-directory where the policies are
      saved.
    checkpoint_range: Optional. If provided, evaluate all checkpoints in
      the range.
    checkpoint_path: Optional sub-directory specifying which checkpoint to
      evaluate. If None, will evaluate the most recent checkpoint.
  """
  tf_env = create_maze_env.TFPyEnvironment(environment)
  observation_spec = [tf_env.observation_spec()]
  action_spec = [tf_env.action_spec()]

  assert max_steps_per_episode, 'max_steps_per_episode need to be set'

  if agent_class.ACTION_TYPE == 'discrete':
    assert False
  else:
    assert agent_class.ACTION_TYPE == 'continuous'

  if meta_agent_class is not None:
    assert agent_class.ACTION_TYPE == meta_agent_class.ACTION_TYPE
    with tf.variable_scope('meta_agent'):
      meta_agent = meta_agent_class(
        observation_spec,
        action_spec,
        tf_env,
      )
  else:
    meta_agent = None

  with tf.variable_scope('uvf_agent'):
    uvf_agent = agent_class(
        observation_spec,
        action_spec,
        tf_env,
    )
    uvf_agent.set_meta_agent(agent=meta_agent)

  with tf.variable_scope('state_preprocess'):
    state_preprocess = state_preprocess_class()

  # run both actor and critic once to ensure networks are initialized
  # and gin configs will be saved
  # pylint: disable=protected-access
  temp_states = tf.expand_dims(
      tf.zeros(
          dtype=uvf_agent._observation_spec.dtype,
          shape=uvf_agent._observation_spec.shape), 0)
  # pylint: enable=protected-access
  temp_actions = uvf_agent.actor_net(temp_states)
  uvf_agent.critic_net(temp_states, temp_actions)

  # create eval_step_fns for each action function
  eval_step_fns = dict()
  meta_agent = uvf_agent.meta_agent
  for meta in [True] + [False] * evaluate_nohrl:
    meta_tag = 'hrl' if meta else 'nohrl'
    uvf_agent.set_meta_agent(meta_agent if meta else None)
    for mode in eval_modes:
      # wrap environment
      wrapped_environment = uvf_agent.get_env_base_wrapper(
          environment, mode=mode)
      action_wrapper = lambda agent_: agent_.action
      action_fn = action_wrapper(uvf_agent)
      meta_action_fn = action_wrapper(meta_agent)
      eval_step_fns['%s_%s' % (mode, meta_tag)] = (get_eval_step(
          uvf_agent=uvf_agent,
          state_preprocess=state_preprocess,
          tf_env=tf_env,
          action_fn=action_fn,
          meta_action_fn=meta_action_fn,
          environment_steps=tf.Variable(
              0, dtype=tf.int64, name='environment_steps'),
          num_episodes=tf.Variable(0, dtype=tf.int64, name='num_episodes'),
          mode=mode), wrapped_environment,)

  model_rollout_fn = None
  if eval_model_rollout:
    model_rollout_fn = get_model_rollout(uvf_agent, tf_env)

  tf.train.get_or_create_global_step()

  if policy_save_dir:
    checkpoint_dir = os.path.join(checkpoint_dir, policy_save_dir)

  tf.logging.info('Evaluating policies at %s', checkpoint_dir)
  tf.logging.info('Running episodes for max %d steps', max_steps_per_episode)

  evaluate_checkpoint_fn = get_evaluate_checkpoint_fn(
      '', eval_dir, eval_step_fns, model_rollout_fn, gamma,
      max_steps_per_episode, num_episodes_eval, num_episodes_videos, tuner_hook,
      generate_videos, generate_summaries, video_settings)

  if checkpoint_path is not None:
    checkpoint_path = os.path.join(checkpoint_dir, checkpoint_path)
    evaluate_checkpoint_fn(checkpoint_path)
  elif checkpoint_range is not None:
    model_files = tf.gfile.Glob(
        os.path.join(checkpoint_dir, 'model.ckpt-*.index'))
    tf.logging.info('Found %s policies at %s', len(model_files), checkpoint_dir)
    model_files = {
        int(f.split('model.ckpt-', 1)[1].split('.', 1)[0]):
        os.path.splitext(f)[0]
        for f in model_files
    }
    model_files = {
        k: v
        for k, v in model_files.items()
        if k >= checkpoint_range[0] and k <= checkpoint_range[1]
    }
    tf.logging.info('Evaluating %d policies at %s',
                    len(model_files), checkpoint_dir)
    for _, checkpoint_path in sorted(model_files.items()):
      evaluate_checkpoint_fn(checkpoint_path)
  else:
    eval_utils.evaluate_checkpoint_repeatedly(
        checkpoint_dir,
        evaluate_checkpoint_fn,
        eval_interval_secs=eval_interval_secs,
        max_number_of_evaluations=max_number_of_evaluations,
        checkpoint_timeout=checkpoint_timeout,
        timeout_fn=timeout_fn)