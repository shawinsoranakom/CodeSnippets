def episode(self):
    """Returns data needed to train and test a single episode.

    Returns:
      (inputs, None, output) where inputs is a dictionary of modality types to
        numpy arrays. The second element is query but we assume that the goal
        is also given as part of observation so it should be None for this task,
        and the outputs is the tuple of ground truth action values with the
        shape of (sequence_length x action_size) that is coming from
        config.output.shape and a numpy array with the shape of
        (sequence_length,) that is 1 if the corresponding element of the
        input and output should be used in the training optimization.

    Raises:
      ValueError: If the output values for env.random_step_sequence is not
        valid.
      ValueError: If the shape of observations coming from the env is not
        consistent with the config.
      ValueError: If there is a modality type specified in the config but the
        environment does not return that.
    """
    # Sequence length is the first dimension of any of the input tensors.
    sequence_length = self._config.inputs.values()[0].shape[0]
    modality_types = self._config.inputs.keys()

    path, _, _, step_outputs = self._env.random_step_sequence(
        max_len=sequence_length)
    target_vertices = [self._env.pose_to_vertex(x) for x in self._env.targets()]

    if len(path) != len(step_outputs):
      raise ValueError('path, and step_outputs should have equal length'
                       ' {}!={}'.format(len(path), len(step_outputs)))

    # Building up observations. observations will be a OrderedDict of
    # modality types. The values are numpy arrays that follow the given shape
    # in the input config for each modality type.
    observations = collections.OrderedDict([k, []] for k in modality_types)
    for step_output in step_outputs:
      obs_dict = step_output[0]
      # Only going over the modality types that are specified in the input
      # config.
      for modality_type in modality_types:
        if modality_type not in obs_dict:
          raise ValueError('modality type is not returned from the environment.'
                           '{} not in {}'.format(modality_type,
                                                 obs_dict.keys()))
        obs = obs_dict[modality_type]
        if np.any(
            obs.shape != tuple(self._config.inputs[modality_type].shape[1:])):
          raise ValueError(
              'The observations should have the same size as speicifed in'
              'config for modality type {}. {} != {}'.format(
                  modality_type, obs.shape,
                  self._config.inputs[modality_type].shape[1:]))
        observations[modality_type].append(obs)

    gt_value = [self._compute_gt_value(v, target_vertices) for v in path]

    # pylint: disable=unbalanced-tuple-unpacking
    gt_value, _, value_mask = _pad_or_clip_array(
        np.array(gt_value),
        sequence_length,
        is_front_clip=False,
        output_mask=True,
    )
    for modality_type, obs in observations.iteritems():
      observations[modality_type], _, mask = _pad_or_clip_array(
          np.array(obs), sequence_length, is_front_clip=False, output_mask=True)
      assert np.all(mask == value_mask)

    return observations, None, (gt_value, value_mask)