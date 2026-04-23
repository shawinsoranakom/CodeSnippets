def __init__(self):
    self.batch_size = FLAGS.batch_size
    self.replay_batch_size = FLAGS.replay_batch_size
    if self.replay_batch_size is None:
      self.replay_batch_size = self.batch_size
    self.num_samples = FLAGS.num_samples

    self.env_str = FLAGS.env
    self.env = gym_wrapper.GymWrapper(self.env_str,
                                      distinct=FLAGS.batch_size // self.num_samples,
                                      count=self.num_samples)
    self.eval_env = gym_wrapper.GymWrapper(
        self.env_str,
        distinct=FLAGS.batch_size // self.num_samples,
        count=self.num_samples)
    self.env_spec = env_spec.EnvSpec(self.env.get_one())

    self.max_step = FLAGS.max_step
    self.cutoff_agent = FLAGS.cutoff_agent
    self.num_steps = FLAGS.num_steps
    self.validation_frequency = FLAGS.validation_frequency

    self.target_network_lag = FLAGS.target_network_lag
    self.sample_from = FLAGS.sample_from
    assert self.sample_from in ['online', 'target']

    self.critic_weight = FLAGS.critic_weight
    self.objective = FLAGS.objective
    self.trust_region_p = FLAGS.trust_region_p
    self.value_opt = FLAGS.value_opt
    assert not self.trust_region_p or self.objective in ['pcl', 'trpo']
    assert self.objective != 'trpo' or self.trust_region_p
    assert self.value_opt is None or self.value_opt == 'None' or \
        self.critic_weight == 0.0
    self.max_divergence = FLAGS.max_divergence

    self.learning_rate = FLAGS.learning_rate
    self.clip_norm = FLAGS.clip_norm
    self.clip_adv = FLAGS.clip_adv
    self.tau = FLAGS.tau
    self.tau_decay = FLAGS.tau_decay
    self.tau_start = FLAGS.tau_start
    self.eps_lambda = FLAGS.eps_lambda
    self.update_eps_lambda = FLAGS.update_eps_lambda
    self.gamma = FLAGS.gamma
    self.rollout = FLAGS.rollout
    self.use_target_values = FLAGS.use_target_values
    self.fixed_std = FLAGS.fixed_std
    self.input_prev_actions = FLAGS.input_prev_actions
    self.recurrent = FLAGS.recurrent
    assert not self.trust_region_p or not self.recurrent
    self.input_time_step = FLAGS.input_time_step
    assert not self.input_time_step or (self.cutoff_agent <= self.max_step)

    self.use_online_batch = FLAGS.use_online_batch
    self.batch_by_steps = FLAGS.batch_by_steps
    self.unify_episodes = FLAGS.unify_episodes
    if self.unify_episodes:
      assert self.batch_size == 1

    self.replay_buffer_size = FLAGS.replay_buffer_size
    self.replay_buffer_alpha = FLAGS.replay_buffer_alpha
    self.replay_buffer_freq = FLAGS.replay_buffer_freq
    assert self.replay_buffer_freq in [-1, 0, 1]
    self.eviction = FLAGS.eviction
    self.prioritize_by = FLAGS.prioritize_by
    assert self.prioritize_by in ['rewards', 'step']
    self.num_expert_paths = FLAGS.num_expert_paths

    self.internal_dim = FLAGS.internal_dim
    self.value_hidden_layers = FLAGS.value_hidden_layers
    self.tf_seed = FLAGS.tf_seed

    self.save_trajectories_dir = FLAGS.save_trajectories_dir
    self.save_trajectories_file = (
        os.path.join(
            self.save_trajectories_dir, self.env_str.replace('-', '_'))
        if self.save_trajectories_dir else None)
    self.load_trajectories_file = FLAGS.load_trajectories_file

    self.hparams = dict((attr, getattr(self, attr))
                        for attr in dir(self)
                        if not attr.startswith('__') and
                        not callable(getattr(self, attr)))