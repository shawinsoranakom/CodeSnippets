def _exploration(self):
    """Generates a random exploration run.

    The function uses the environment to generate a run.

    Returns:
      A tuple of numpy arrays. The i-th array contains observation of type and
      shape as specified in config.inputs[i].
      A list of states along the exploration path.
      A list of vertex indices corresponding to the path of the exploration.
    """
    in_seq_len = self._config.inputs.values()[0].shape[0]
    path, _, states, step_outputs = self._env.random_step_sequence(
        min_len=in_seq_len)
    obs = {modality_type: [] for modality_type in self._config.inputs}
    for o in step_outputs:
      step_obs, _, done, _ = o
      # It is expected that each value of step_obs is a dict of observations,
      # whose dimensions are consistent with the config.inputs sizes.
      for modality_type in self._config.inputs:
        assert modality_type in step_obs, '{}'.format(type(step_obs))
        o = step_obs[modality_type]
        i = self._config.inputs[modality_type]
        assert len(o.shape) == len(i.shape) - 1
        for dim_o, dim_i in zip(o.shape, i.shape[1:]):
          assert dim_o == dim_i, '{} != {}'.format(dim_o, dim_i)
        obs[modality_type].append(o)
      if done:
        break

    if not obs:
      return obs, states, path

    max_path_len = int(
        round(in_seq_len * float(len(path)) / float(len(obs.values()[0]))))
    path = path[-max_path_len:]
    states = states[-in_seq_len:]

    # The above obs is a list of tuples of np,array. Re-format them as tuple of
    # np.array, each array containing all observations from all steps.
    def regroup(obs, i):
      """Regroups observations.

      Args:
        obs: a list of tuples of same size. The k-th tuple contains all the
          observations from k-th step. Each observation is a numpy array.
        i: the index of the observation in each tuple to be grouped.

      Returns:
        A numpy array of shape config.inputs[i] which contains all i-th
        observations from all steps. These are concatenated along the first
        dimension. In addition, if the number of observations is different from
        the one specified in config.inputs[i].shape[0], then the array is either
        padded from front or clipped.
      """
      grouped_obs = np.concatenate(
          [np.expand_dims(o, axis=0) for o in obs[i]], axis=0)
      in_seq_len = self._config.inputs[i].shape[0]
      # pylint: disable=unbalanced-tuple-unpacking
      grouped_obs, _ = _pad_or_clip_array(
          grouped_obs, in_seq_len, is_front_clip=True)
      return grouped_obs

    all_obs = {i: regroup(obs, i) for i in self._config.inputs}

    return all_obs, states, path