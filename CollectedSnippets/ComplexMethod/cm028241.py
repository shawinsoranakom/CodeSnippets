def _build_initializer(initializer, build_for_keras=False):
  """Build a tf initializer from config.

  Args:
    initializer: hyperparams_pb2.Hyperparams.regularizer proto.
    build_for_keras: Whether the initializers should be built for Keras
      operators. If false builds for Slim.

  Returns:
    tf initializer or string corresponding to the tf keras initializer name.

  Raises:
    ValueError: On unknown initializer.
  """
  initializer_oneof = initializer.WhichOneof('initializer_oneof')
  if initializer_oneof == 'truncated_normal_initializer':
    return tf.truncated_normal_initializer(
        mean=initializer.truncated_normal_initializer.mean,
        stddev=initializer.truncated_normal_initializer.stddev)
  if initializer_oneof == 'random_normal_initializer':
    return tf.random_normal_initializer(
        mean=initializer.random_normal_initializer.mean,
        stddev=initializer.random_normal_initializer.stddev)
  if initializer_oneof == 'variance_scaling_initializer':
    enum_descriptor = (hyperparams_pb2.VarianceScalingInitializer.
                       DESCRIPTOR.enum_types_by_name['Mode'])
    mode = enum_descriptor.values_by_number[initializer.
                                            variance_scaling_initializer.
                                            mode].name
    if build_for_keras:
      if initializer.variance_scaling_initializer.uniform:
        return tf.variance_scaling_initializer(
            scale=initializer.variance_scaling_initializer.factor,
            mode=mode.lower(),
            distribution='uniform')
      else:
        # In TF 1.9 release and earlier, the truncated_normal distribution was
        # not supported correctly. So, in these earlier versions of tensorflow,
        # the ValueError will be raised, and we manually truncate the
        # distribution scale.
        #
        # It is insufficient to just set distribution to `normal` from the
        # start, because the `normal` distribution in newer Tensorflow versions
        # creates a truncated distribution, whereas it created untruncated
        # distributions in older versions.
        try:
          return tf.variance_scaling_initializer(
              scale=initializer.variance_scaling_initializer.factor,
              mode=mode.lower(),
              distribution='truncated_normal')
        except ValueError:
          truncate_constant = 0.87962566103423978
          truncated_scale = initializer.variance_scaling_initializer.factor / (
              truncate_constant * truncate_constant
          )
          return tf.variance_scaling_initializer(
              scale=truncated_scale,
              mode=mode.lower(),
              distribution='normal')

    else:
      return slim.variance_scaling_initializer(
          factor=initializer.variance_scaling_initializer.factor,
          mode=mode,
          uniform=initializer.variance_scaling_initializer.uniform)
  if initializer_oneof == 'keras_initializer_by_name':
    if build_for_keras:
      return initializer.keras_initializer_by_name
    else:
      raise ValueError(
          'Unsupported non-Keras usage of keras_initializer_by_name: {}'.format(
              initializer.keras_initializer_by_name))
  if initializer_oneof is None:
    return None
  raise ValueError('Unknown initializer function: {}'.format(
      initializer_oneof))