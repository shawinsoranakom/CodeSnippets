def _obtain_input_shape(
    input_shape,
    default_size,
    min_size,
    data_format,
    require_flatten):
  """Internal utility to compute/validate an ImageNet model's input shape.

  Args:
      input_shape: either None (will return the default network input shape),
          or a user-provided shape to be validated.
      default_size: default input width/height for the model.
      min_size: minimum input width/height accepted by the model.
      data_format: image data format to use.
      require_flatten: whether the model is expected to
          be linked to a classifier via a Flatten layer.

  Returns:
      An integer shape tuple (may include None entries).

  Raises:
      ValueError: in case of invalid argument values.
  """
  if input_shape and len(input_shape) == 3:
    if data_format == 'channels_first':
      if input_shape[0] not in {1, 3}:
        warnings.warn(
            'This model usually expects 1 or 3 input channels. '
            'However, it was passed an input_shape with ' +
            str(input_shape[0]) + ' input channels.')
      default_shape = (input_shape[0], default_size, default_size)
    else:
      if input_shape[-1] not in {1, 3}:
        warnings.warn(
            'This model usually expects 1 or 3 input channels. '
            'However, it was passed an input_shape with ' +
            str(input_shape[-1]) + ' input channels.')
      default_shape = (default_size, default_size, input_shape[-1])
  else:
    if data_format == 'channels_first':
      default_shape = (3, default_size, default_size)
    else:
      default_shape = (default_size, default_size, 3)
  if input_shape:
    if data_format == 'channels_first':
      if input_shape is not None:
        if len(input_shape) != 3:
          raise ValueError(
              '`input_shape` must be a tuple of three integers.')
        if ((input_shape[1] is not None and input_shape[1] < min_size) or
            (input_shape[2] is not None and input_shape[2] < min_size)):
          raise ValueError('Input size must be at least ' +
                           str(min_size) + 'x' + str(min_size) +
                           '; got `input_shape=' +
                           str(input_shape) + '`')
    else:
      if input_shape is not None:
        if len(input_shape) != 3:
          raise ValueError(
              '`input_shape` must be a tuple of three integers.')
        if ((input_shape[0] is not None and input_shape[0] < min_size) or
            (input_shape[1] is not None and input_shape[1] < min_size)):
          raise ValueError('Input size must be at least ' +
                           str(min_size) + 'x' + str(min_size) +
                           '; got `input_shape=' +
                           str(input_shape) + '`')
  else:
    if require_flatten:
      input_shape = default_shape
    else:
      if data_format == 'channels_first':
        input_shape = (3, None, None)
      else:
        input_shape = (None, None, 3)
  if require_flatten:
    if None in input_shape:
      raise ValueError('If `include_top` is True, '
                       'you should specify a static `input_shape`. '
                       'Got `input_shape=' + str(input_shape) + '`')
  return input_shape