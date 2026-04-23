def crop_image(
    frames: tf.Tensor,
    target_height: int,
    target_width: int,
    random: bool = False,
    num_crops: int = 1,
    seed: Optional[int] = None,
) -> tf.Tensor:
  """Crops the image sequence of images.

  If requested size is bigger than image size, image is padded with 0. If not
  random cropping, a central crop is performed if num_crops is 1.

  Args:
    frames: A Tensor of dimension [timesteps, in_height, in_width, channels].
    target_height: Target cropped image height.
    target_width: Target cropped image width.
    random: A boolean indicating if crop should be randomized.
    num_crops: Number of crops (support 1 for central crop and 3 for 3-crop).
    seed: A deterministic seed to use when random cropping.

  Returns:
    A Tensor of shape [timesteps, out_height, out_width, channels] of type uint8
    with the cropped images.
  """
  if random:
    # Random spatial crop.
    shape = tf.shape(frames)
    # If a static_shape is available (e.g. when using this method from add_image
    # method), it will be used to have an output tensor with static shape.
    static_shape = frames.shape.as_list()
    seq_len = shape[0] if static_shape[0] is None else static_shape[0]
    channels = shape[3] if static_shape[3] is None else static_shape[3]
    frames = tf.image.random_crop(
        frames, (seq_len, target_height, target_width, channels), seed)
  else:
    if num_crops == 1:
      # Central crop or pad.
      frames = tf.image.resize_with_crop_or_pad(frames, target_height,
                                                target_width)

    elif num_crops == 3:
      # Three-crop evaluation.
      shape = tf.shape(frames)
      static_shape = frames.shape.as_list()
      seq_len = shape[0] if static_shape[0] is None else static_shape[0]
      height = shape[1] if static_shape[1] is None else static_shape[1]
      width = shape[2] if static_shape[2] is None else static_shape[2]
      channels = shape[3] if static_shape[3] is None else static_shape[3]

      size = tf.convert_to_tensor(
          (seq_len, target_height, target_width, channels))

      offset_1 = tf.broadcast_to([0, 0, 0, 0], [4])
      # pylint:disable=g-long-lambda
      offset_2 = tf.cond(
          tf.greater_equal(height, width),
          true_fn=lambda: tf.broadcast_to([
              0, tf.cast(height, tf.float32) / 2 - target_height // 2, 0, 0
          ], [4]),
          false_fn=lambda: tf.broadcast_to([
              0, 0, tf.cast(width, tf.float32) / 2 - target_width // 2, 0
          ], [4]))
      offset_3 = tf.cond(
          tf.greater_equal(height, width),
          true_fn=lambda: tf.broadcast_to(
              [0, tf.cast(height, tf.float32) - target_height, 0, 0], [4]),
          false_fn=lambda: tf.broadcast_to(
              [0, 0, tf.cast(width, tf.float32) - target_width, 0], [4]))
      # pylint:disable=g-long-lambda

      crops = []
      for offset in [offset_1, offset_2, offset_3]:
        offset = tf.cast(tf.math.round(offset), tf.int32)
        crops.append(tf.slice(frames, offset, size))
      frames = tf.concat(crops, axis=0)

    else:
      raise NotImplementedError(
          f"Only 1-crop and 3-crop are supported. Found {num_crops!r}.")

  return frames