def setup_placeholders(self):
    """Create the Tensorflow placeholders."""
    # summary placeholder
    self.avg_episode_reward = tf.placeholder(
        tf.float32, [], 'avg_episode_reward')
    self.greedy_episode_reward = tf.placeholder(
        tf.float32, [], 'greedy_episode_reward')

    # sampling placeholders
    self.internal_state = tf.placeholder(tf.float32,
                                         [None, self.policy.rnn_state_dim],
                                         'internal_state')

    self.single_observation = []
    for i, (obs_dim, obs_type) in enumerate(self.env_spec.obs_dims_and_types):
      if self.env_spec.is_discrete(obs_type):
        self.single_observation.append(
            tf.placeholder(tf.int32, [None], 'obs%d' % i))
      elif self.env_spec.is_box(obs_type):
        self.single_observation.append(
            tf.placeholder(tf.float32, [None, obs_dim], 'obs%d' % i))
      else:
        assert False

    self.single_action = []
    for i, (action_dim, action_type) in \
        enumerate(self.env_spec.act_dims_and_types):
      if self.env_spec.is_discrete(action_type):
        self.single_action.append(
            tf.placeholder(tf.int32, [None], 'act%d' % i))
      elif self.env_spec.is_box(action_type):
        self.single_action.append(
            tf.placeholder(tf.float32, [None, action_dim], 'act%d' % i))
      else:
        assert False

    # training placeholders
    self.observations = []
    for i, (obs_dim, obs_type) in enumerate(self.env_spec.obs_dims_and_types):
      if self.env_spec.is_discrete(obs_type):
        self.observations.append(
            tf.placeholder(tf.int32, [None, None], 'all_obs%d' % i))
      else:
        self.observations.append(
            tf.placeholder(tf.float32, [None, None, obs_dim], 'all_obs%d' % i))

    self.actions = []
    self.other_logits = []
    for i, (action_dim, action_type) in \
        enumerate(self.env_spec.act_dims_and_types):
      if self.env_spec.is_discrete(action_type):
        self.actions.append(
            tf.placeholder(tf.int32, [None, None], 'all_act%d' % i))
      if self.env_spec.is_box(action_type):
        self.actions.append(
            tf.placeholder(tf.float32, [None, None, action_dim],
                           'all_act%d' % i))
      self.other_logits.append(
          tf.placeholder(tf.float32, [None, None, None],
                         'other_logits%d' % i))

    self.rewards = tf.placeholder(tf.float32, [None, None], 'rewards')
    self.terminated = tf.placeholder(tf.float32, [None], 'terminated')
    self.pads = tf.placeholder(tf.float32, [None, None], 'pads')

    self.prev_log_probs = tf.placeholder(tf.float32, [None, None],
                                         'prev_log_probs')