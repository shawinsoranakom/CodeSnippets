def pad_to_bounding_box(image, offset_height, offset_width, target_height,
                        target_width, pad_value):
  """Pads the given image with the given pad_value.

  Works like tf.image.pad_to_bounding_box, except it can pad the image
  with any given arbitrary pad value and also handle images whose sizes are not
  known during graph construction.

  Args:
    image: 3-D tensor with shape [height, width, channels]
    offset_height: Number of rows of zeros to add on top.
    offset_width: Number of columns of zeros to add on the left.
    target_height: Height of output image.
    target_width: Width of output image.
    pad_value: Value to pad the image tensor with.

  Returns:
    3-D tensor of shape [target_height, target_width, channels].

  Raises:
    ValueError: If the shape of image is incompatible with the offset_* or
    target_* arguments.
  """
  with tf.name_scope(None, 'pad_to_bounding_box', [image]):
    image = tf.convert_to_tensor(image, name='image')
    original_dtype = image.dtype
    if original_dtype != tf.float32 and original_dtype != tf.float64:
      # If image dtype is not float, we convert it to int32 to avoid overflow.
      image = tf.cast(image, tf.int32)
    image_rank_assert = tf.Assert(
        tf.logical_or(
            tf.equal(tf.rank(image), 3),
            tf.equal(tf.rank(image), 4)),
        ['Wrong image tensor rank.'])
    with tf.control_dependencies([image_rank_assert]):
      image -= pad_value
    image_shape = image.get_shape()
    is_batch = True
    if image_shape.ndims == 3:
      is_batch = False
      image = tf.expand_dims(image, 0)
    elif image_shape.ndims is None:
      is_batch = False
      image = tf.expand_dims(image, 0)
      image.set_shape([None] * 4)
    elif image.get_shape().ndims != 4:
      raise ValueError('Input image must have either 3 or 4 dimensions.')
    _, height, width, _ = _image_dimensions(image, rank=4)
    target_width_assert = tf.Assert(
        tf.greater_equal(
            target_width, width),
        ['target_width must be >= width'])
    target_height_assert = tf.Assert(
        tf.greater_equal(target_height, height),
        ['target_height must be >= height'])
    with tf.control_dependencies([target_width_assert]):
      after_padding_width = target_width - offset_width - width
    with tf.control_dependencies([target_height_assert]):
      after_padding_height = target_height - offset_height - height
    offset_assert = tf.Assert(
        tf.logical_and(
            tf.greater_equal(after_padding_width, 0),
            tf.greater_equal(after_padding_height, 0)),
        ['target size not possible with the given target offsets'])
    batch_params = tf.stack([0, 0])
    height_params = tf.stack([offset_height, after_padding_height])
    width_params = tf.stack([offset_width, after_padding_width])
    channel_params = tf.stack([0, 0])
    with tf.control_dependencies([offset_assert]):
      paddings = tf.stack([batch_params, height_params, width_params,
                           channel_params])
    padded = tf.pad(image, paddings)
    if not is_batch:
      padded = tf.squeeze(padded, axis=[0])
    outputs = padded + pad_value
    if outputs.dtype != original_dtype:
      outputs = tf.cast(outputs, original_dtype)
    return outputs