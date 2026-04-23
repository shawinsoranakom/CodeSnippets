def _sample_obs(self,
                  indices,
                  observations,
                  observation_states,
                  path_to_obs,
                  max_obs_index=None,
                  use_exploration_obs=True):
    """Samples one observation which corresponds to vertex_index in path.

    In addition, the sampled observation must have index in observations less
    than max_obs_index. If these two conditions cannot be satisfied the
    function returns None.

    Args:
      indices: a list of integers.
      observations: a list of numpy arrays containing all the observations.
      observation_states: a list of numpy arrays, each array representing the
        state of the observation.
      path_to_obs: a dict of path indices to lists of observation indices.
      max_obs_index: an integer.
      use_exploration_obs: if True, then the observation is sampled among the
        specified observations, otherwise it is obtained from the environment.
    Returns:
      A tuple of:
        -- A numpy array of size width x height x 3 representing the sampled
          observation.
        -- The index of the sampld observation among the input observations.
        -- The state at which the observation is captured.
    Raises:
      ValueError: if the observation and observation_states lists are of
        different lengths.
    """
    if len(observations) != len(observation_states):
      raise ValueError('observation and observation_states lists must have '
                       'equal lengths')
    if not indices:
      return None, None, None
    vertex_index = self._rng.choice(indices)
    if use_exploration_obs:
      obs_indices = path_to_obs[vertex_index]

      if max_obs_index is not None:
        obs_indices = [i for i in obs_indices if i < max_obs_index]

      if obs_indices:
        index = self._rng.choice(obs_indices)
        if self._add_query_noise:
          xytheta = self._perturb_state(observation_states[index],
                                        self._query_noise_var)
          return self._env.observation(xytheta), index, xytheta
        else:
          return observations[index], index, observation_states[index]
      else:
        return None, None, None
    else:
      xy = self._env.vertex_to_pose(vertex_index)
      xytheta = np.array([xy[0], xy[1], 0.0])
      xytheta = self._perturb_state(xytheta, self._query_noise_var)
      return self._env.observation(xytheta), None, xytheta