def _initializer(shape, dtype=tf.float32, partition_info=None):  # pylint: disable=unused-argument
    """Initializer op."""

    if dtype != tf.float32 and dtype != tf.bfloat16:
      raise ValueError(
          'Input tensor data type has to be tf.float32 or tf.bfloat16.')
    if len(shape) != 5:
      raise ValueError('Input tensor has to be 5-D.')
    if shape[3] != shape[4]:
      raise ValueError('Input and output channel dimensions must be the same.')
    if shape[1] != 1 or shape[2] != 1:
      raise ValueError('Spatial kernel sizes must be 1 (pointwise conv).')
    if shape[0] % 2 == 0:
      raise ValueError('Temporal kernel size has to be odd.')

    center_pos = int(shape[0] / 2)
    init_mat = np.zeros(
        [shape[0], shape[1], shape[2], shape[3], shape[4]], dtype=np.float32)
    for i in range(0, shape[3]):
      init_mat[center_pos, 0, 0, i, i] = 1.0

    init_op = tf.constant(init_mat, dtype=dtype)
    return init_op