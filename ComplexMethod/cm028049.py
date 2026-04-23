def __init__(self,
               tf_env,
               context_ranges=None,
               context_shapes=None,
               state_indices=None,
               variable_indices=None,
               gamma_index=None,
               settable_context=False,
               timers=None,
               samplers=None,
               reward_weights=None,
               reward_fn=None,
               random_sampler_mode='random',
               normalizers=None,
               context_transition_fn=None,
               context_multi_transition_fn=None,
               meta_action_every_n=None):
    self._tf_env = tf_env
    self.variable_indices = variable_indices
    self.gamma_index = gamma_index
    self._settable_context = settable_context
    self.timers = timers
    self._context_transition_fn = context_transition_fn
    self._context_multi_transition_fn = context_multi_transition_fn
    self._random_sampler_mode = random_sampler_mode

    # assign specs
    self._obs_spec = self._tf_env.observation_spec()
    self._context_shapes = tuple([
        shape if shape is not None else self._obs_spec.shape
        for shape in context_shapes
    ])
    self.context_specs = tuple([
        specs.TensorSpec(dtype=self._obs_spec.dtype, shape=shape)
        for shape in self._context_shapes
    ])
    if context_ranges is not None:
      self.context_ranges = context_ranges
    else:
      self.context_ranges = [None] * len(self._context_shapes)

    self.context_as_action_specs = tuple([
        specs.BoundedTensorSpec(
            shape=shape,
            dtype=(tf.float32 if self._obs_spec.dtype in
                   [tf.float32, tf.float64] else self._obs_spec.dtype),
            minimum=context_range[0],
            maximum=context_range[-1])
        for shape, context_range in zip(self._context_shapes, self.context_ranges)
    ])

    if state_indices is not None:
      self.state_indices = state_indices
    else:
      self.state_indices = [None] * len(self._context_shapes)
    if self.variable_indices is not None and self.n != len(
        self.variable_indices):
      raise ValueError(
          'variable_indices (%s) must have the same length as contexts (%s).' %
          (self.variable_indices, self.context_specs))
    assert self.n == len(self.context_ranges)
    assert self.n == len(self.state_indices)

    # assign reward/sampler fns
    self._sampler_fns = dict()
    self._samplers = dict()
    self._reward_fns = dict()

    # assign reward fns
    self._add_custom_reward_fns()
    reward_weights = reward_weights or None
    self._reward_fn = self._make_reward_fn(reward_fn, reward_weights)

    # assign samplers
    self._add_custom_sampler_fns()
    for mode, sampler_fns in samplers.items():
      self._make_sampler_fn(sampler_fns, mode)

    # create normalizers
    if normalizers is None:
      self._normalizers = [None] * len(self.context_specs)
    else:
      self._normalizers = [
          normalizer(tf.zeros(shape=spec.shape, dtype=spec.dtype))
          if normalizer is not None else None
          for normalizer, spec in zip(normalizers, self.context_specs)
      ]
    assert self.n == len(self._normalizers)

    self.meta_action_every_n = meta_action_every_n

    # create vars
    self.context_vars = {}
    self.timer_vars = {}
    self.create_vars(self.VAR_NAME)
    self.t = tf.Variable(
        tf.zeros(shape=(), dtype=tf.int32), name='num_timer_steps')