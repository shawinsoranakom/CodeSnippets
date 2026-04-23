def resize_and_crop(
    frames: tf.Tensor,
    min_resize: int,
    crop_size: int,
    is_flow: bool = False,
    is_random: bool = False,
    seed: Optional[int] = None,
    state: Optional[MutableMapping[str, Any]] = None) -> tf.Tensor:
  """Resizes the smallest and crops frames.

  Args:
    frames: A Tensor of dimension [timesteps, input_h, input_w, channels].
    min_resize: Minimum size of the final image dimensions.
    crop_size: Crop size of the final image dimensions.
    is_flow: If is flow, will modify the raw values to account for the resize.
      For example, if the flow image is resized by a factor k, we need to
      multiply the flow values by the same factor k since one pixel displacement
      in the resized image corresponds to only 1/k pixel displacement in the
      original image.
    is_random: Whether perform random crop or central crop.
    seed: Random seed.
    state: the dictionary contains data processing states.
  Returns:
    A Tensor of shape [timesteps, output_h, output_w, channels] of type
      frames.dtype where min(output_h, output_w) = min_resize.
  """
  if is_flow and frames.dtype != tf.float32:
    raise ValueError('If is_flow, frames should be given in float32.')

  if min_resize < crop_size:
    raise ValueError('min_resize should be larger than crop_size. Got '
                     f'({min_resize}, {crop_size}).')

  if is_random:
    min_resize = tf.random.uniform((),
                                   minval=min_resize,
                                   maxval=_VGG_EXPANSION_RATIO * min_resize,
                                   dtype=tf.float32)

  shape = tf.shape(input=frames)
  image_size = tf.cast(shape[1:3], tf.float32)
  input_h = image_size[0]
  input_w = image_size[1]

  scale = tf.cast(min_resize / input_h, tf.float32)
  scale = tf.maximum(scale, tf.cast(min_resize / input_w, tf.float32))

  scale_h = input_h * scale
  scale_w = input_w * scale

  def resize_fn():
    """Function wraper to perform bilinear image resizing."""
    frames_resized = tf.image.resize(
        frames, (scale_h, scale_w), method=tf.image.ResizeMethod.BILINEAR)
    return tf.cast(frames_resized, frames.dtype)

  should_resize = tf.math.logical_or(tf.not_equal(input_w, scale_w),
                                     tf.not_equal(input_h, scale_h))
  frames = tf.cond(
      pred=should_resize, true_fn=resize_fn, false_fn=lambda: frames)

  if is_flow:
    # Apply a multiplier to keep the right magnitude in the flow.
    frames = frames * tf.cast(scale_h / input_h, tf.float32)

  shape = tf.shape(input=frames)
  image_size = tf.cast(shape[1:3], tf.float32)
  # If a static_shape is available (e.g. when using this method from add_image
  # method), it will be used to have an output tensor with static shape.
  static_shape = frames.shape.as_list()
  seq_len = shape[0] if static_shape[0] is None else static_shape[0]
  channels = shape[3] if static_shape[3] is None else static_shape[3]
  size = tf.convert_to_tensor(value=(seq_len, crop_size, crop_size, channels))
  if is_random:
    # Limit of possible offset in order to fit the entire crop:
    # [1, input_h - target_h + 1, input_w - target_w + 1, 1].
    limit = shape - size + 1
    offset = tf.random.uniform(
        shape=(4,),
        dtype=tf.int32,
        maxval=tf.int32.max,
        seed=seed) % limit  # [0, offset_h, offset_w, 0]
  else:
    # Central spatial crop.
    offset = tf.convert_to_tensor(
        (0, tf.cast((image_size[0] - crop_size) / 2, dtype=tf.int32),
         tf.cast((image_size[1] - crop_size) / 2, dtype=tf.int32), 0))

  frames = tf.slice(frames, offset, size)

  if state is not None:
    # Note: image_info encodes the information of the image and the applied
    # preprocessing. It is in the format of
    # [[original_height, original_width], [desired_height, desired_width],
    #  [y_scale, x_scale], [y_offset, x_offset]],
    # where [desired_height, desired_width] is the actual scaled image size,
    # and [y_scale, x_scale] is the scaling factor, which is the ratio of scaled
    # dimension / original dimension. [y_offset, x_offset] is the upper-left
    # coordinates to perform image cropping.
    image_info = tf.stack([
        tf.convert_to_tensor((input_h, input_w), tf.float32),
        tf.convert_to_tensor((crop_size, crop_size), tf.float32),
        tf.convert_to_tensor((scale, scale), tf.float32),
        tf.cast(offset[1:3], tf.float32)])

    if 'image_info' not in state:
      state['image_info'] = image_info
    else:
      update_image_info(state, image_info)

  return frames