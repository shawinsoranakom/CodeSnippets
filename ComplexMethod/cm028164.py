def __init__(self, env, try_combining_actions=True,
               discretize_actions=None):
    self.discretize_actions = discretize_actions

    # figure out observation space
    self.obs_space = env.observation_space
    self.obs_dims, self.obs_types, self.obs_info = get_spaces(self.obs_space)

    # figure out action space
    self.act_space = env.action_space
    self.act_dims, self.act_types, self.act_info = get_spaces(self.act_space)

    if self.discretize_actions:
      self._act_dims = self.act_dims[:]
      self._act_types = self.act_types[:]
      self.act_dims = []
      self.act_types = []
      for i, (dim, typ) in enumerate(zip(self._act_dims, self._act_types)):
        if typ == spaces.discrete:
          self.act_dims.append(dim)
          self.act_types.append(spaces.discrete)
        elif typ == spaces.box:
          for _ in xrange(dim):
            self.act_dims.append(self.discretize_actions)
            self.act_types.append(spaces.discrete)
    else:
      self._act_dims = None
      self._act_types = None

    if (try_combining_actions and
        all(typ == spaces.discrete for typ in self.act_types)):
      self.combine_actions = True
      self.orig_act_dims = self.act_dims[:]
      self.orig_act_types = self.act_types[:]
      total_act_dim = 1
      for dim in self.act_dims:
        total_act_dim *= dim
      self.act_dims = [total_act_dim]
      self.act_types = [spaces.discrete]
    else:
      self.combine_actions = False

    self.obs_dims_and_types = tuple(zip(self.obs_dims, self.obs_types))
    self.act_dims_and_types = tuple(zip(self.act_dims, self.act_types))

    self.total_obs_dim = sum(self.obs_dims)
    self.total_sampling_act_dim = sum(self.sampling_dim(dim, typ)
                                      for dim, typ in self.act_dims_and_types)
    self.total_sampled_act_dim = sum(self.act_dims)