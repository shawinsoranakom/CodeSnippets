def resize_to_range(image,
                    masks=None,
                    min_dimension=None,
                    max_dimension=None,
                    method=tf.image.ResizeMethod.BILINEAR,
                    pad_to_max_dimension=False,
                    per_channel_pad_value=(0, 0, 0)):
  """Resizes an image so its dimensions are within the provided value.

  The output size can be described by two cases:
  1. If the image can be rescaled so its minimum dimension is equal to the
     provided value without the other dimension exceeding max_dimension,
     then do so.
  2. Otherwise, resize so the largest dimension is equal to max_dimension.

  Args:
    image: A 3D tensor of shape [height, width, channels]
    masks: (optional) rank 3 float32 tensor with shape
           [num_instances, height, width] containing instance masks.
    min_dimension: (optional) (scalar) desired size of the smaller image
                   dimension.
    max_dimension: (optional) (scalar) maximum allowed size
                   of the larger image dimension.
    method: (optional) interpolation method used in resizing. Defaults to
            BILINEAR.
    pad_to_max_dimension: Whether to resize the image and pad it with zeros
      so the resulting image is of the spatial size
      [max_dimension, max_dimension]. If masks are included they are padded
      similarly.
    per_channel_pad_value: A tuple of per-channel scalar value to use for
      padding. By default pads zeros.

  Returns:
    Note that the position of the resized_image_shape changes based on whether
    masks are present.
    resized_image: A 3D tensor of shape [new_height, new_width, channels],
      where the image has been resized (with bilinear interpolation) so that
      min(new_height, new_width) == min_dimension or
      max(new_height, new_width) == max_dimension.
    resized_masks: If masks is not None, also outputs masks. A 3D tensor of
      shape [num_instances, new_height, new_width].
    resized_image_shape: A 1D tensor of shape [3] containing shape of the
      resized image.

  Raises:
    ValueError: if the image is not a 3D tensor.
  """
  if len(image.get_shape()) != 3:
    raise ValueError('Image should be 3D tensor')

  def _resize_landscape_image(image):
    # resize a landscape image
    return tf.image.resize(
        image, tf.stack([min_dimension, max_dimension]), method=method,
        preserve_aspect_ratio=True)

  def _resize_portrait_image(image):
    # resize a portrait image
    return tf.image.resize(
        image, tf.stack([max_dimension, min_dimension]), method=method,
        preserve_aspect_ratio=True)

  with tf.name_scope('ResizeToRange'):
    if image.get_shape().is_fully_defined():
      if image.get_shape()[0] < image.get_shape()[1]:
        new_image = _resize_landscape_image(image)
      else:
        new_image = _resize_portrait_image(image)
      new_size = tf.constant(new_image.get_shape().as_list())
    else:
      new_image = tf.cond(
          tf.less(tf.shape(image)[0], tf.shape(image)[1]),
          lambda: _resize_landscape_image(image),
          lambda: _resize_portrait_image(image))
      new_size = tf.shape(new_image)

    if pad_to_max_dimension:
      channels = tf.unstack(new_image, axis=2)
      if len(channels) != len(per_channel_pad_value):
        raise ValueError('Number of channels must be equal to the length of '
                         'per-channel pad value.')
      new_image = tf.stack(
          [
              tf.pad(  # pylint: disable=g-complex-comprehension
                  channels[i], [[0, max_dimension - new_size[0]],
                                [0, max_dimension - new_size[1]]],
                  constant_values=per_channel_pad_value[i])
              for i in range(len(channels))
          ],
          axis=2)
      new_image.set_shape([max_dimension, max_dimension, len(channels)])

    result = [new_image, new_size]
    if masks is not None:
      new_masks = tf.expand_dims(masks, 3)
      new_masks = tf.image.resize(
          new_masks,
          new_size[:-1],
          method=tf.image.ResizeMethod.NEAREST_NEIGHBOR)
      if pad_to_max_dimension:
        new_masks = tf.image.pad_to_bounding_box(
            new_masks, 0, 0, max_dimension, max_dimension)
      new_masks = tf.squeeze(new_masks, 3)
      result.append(new_masks)

    return result