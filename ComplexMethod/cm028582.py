def _process_image(image: tf.Tensor,
                   is_training: bool = True,
                   is_ssl: bool = False,
                   num_frames: int = 32,
                   stride: int = 1,
                   num_test_clips: int = 1,
                   min_resize: int = 256,
                   crop_size: int = 224,
                   num_crops: int = 1,
                   zero_centering_image: bool = False,
                   seed: Optional[int] = None) -> tf.Tensor:
  """Processes a serialized image tensor.

  Args:
    image: Input Tensor of shape [timesteps] and type tf.string of serialized
      frames.
    is_training: Whether or not in training mode. If True, random sample, crop
      and left right flip is used.
    is_ssl: Whether or not in self-supervised pre-training mode.
    num_frames: Number of frames per subclip.
    stride: Temporal stride to sample frames.
    num_test_clips: Number of test clips (1 by default). If more than 1, this
      will sample multiple linearly spaced clips within each video at test time.
      If 1, then a single clip in the middle of the video is sampled. The clips
      are aggreagated in the batch dimension.
    min_resize: Frames are resized so that min(height, width) is min_resize.
    crop_size: Final size of the frame after cropping the resized frames. Both
      height and width are the same.
    num_crops: Number of crops to perform on the resized frames.
    zero_centering_image: If True, frames are normalized to values in [-1, 1].
      If False, values in [0, 1].
    seed: A deterministic seed to use when sampling.

  Returns:
    Processed frames. Tensor of shape
      [num_frames * num_test_clips, crop_size, crop_size, 3].
  """
  # Validate parameters.
  if is_training and num_test_clips != 1:
    logging.warning(
        '`num_test_clips` %d is ignored since `is_training` is `True`.',
        num_test_clips)

  # Temporal sampler.
  if is_training:
    # Sampler for training.
    if is_ssl:
      # Sample two clips from linear decreasing distribution.
      image = video_ssl_preprocess_ops.sample_ssl_sequence(
          image, num_frames, True, stride)
    else:
      # Sample random clip.
      image = preprocess_ops_3d.sample_sequence(image, num_frames, True, stride)

  else:
    # Sampler for evaluation.
    if num_test_clips > 1:
      # Sample linspace clips.
      image = preprocess_ops_3d.sample_linspace_sequence(image, num_test_clips,
                                                         num_frames, stride)
    else:
      # Sample middle clip.
      image = preprocess_ops_3d.sample_sequence(image, num_frames, False,
                                                stride)

  # Decode JPEG string to tf.uint8.
  image = preprocess_ops_3d.decode_jpeg(image, 3)

  if is_training:
    # Standard image data augmentation: random resized crop and random flip.
    if is_ssl:
      image_1, image_2 = tf.split(image, num_or_size_splits=2, axis=0)
      image_1 = preprocess_ops_3d.random_crop_resize(
          image_1, crop_size, crop_size, num_frames, 3, (0.5, 2), (0.3, 1))
      image_1 = preprocess_ops_3d.random_flip_left_right(image_1, seed)
      image_2 = preprocess_ops_3d.random_crop_resize(
          image_2, crop_size, crop_size, num_frames, 3, (0.5, 2), (0.3, 1))
      image_2 = preprocess_ops_3d.random_flip_left_right(image_2, seed)

    else:
      image = preprocess_ops_3d.random_crop_resize(
          image, crop_size, crop_size, num_frames, 3, (0.5, 2), (0.3, 1))
      image = preprocess_ops_3d.random_flip_left_right(image, seed)
  else:
    # Resize images (resize happens only if necessary to save compute).
    image = preprocess_ops_3d.resize_smallest(image, min_resize)
    # Three-crop of the frames.
    image = preprocess_ops_3d.crop_image(image, crop_size, crop_size, False,
                                         num_crops)

  # Cast the frames in float32, normalizing according to zero_centering_image.
  if is_training and is_ssl:
    image_1 = preprocess_ops_3d.normalize_image(image_1, zero_centering_image)
    image_2 = preprocess_ops_3d.normalize_image(image_2, zero_centering_image)

  else:
    image = preprocess_ops_3d.normalize_image(image, zero_centering_image)

  # Self-supervised pre-training augmentations.
  if is_training and is_ssl:
    if zero_centering_image:
      image_1 = 0.5 * (image_1 + 1.0)
      image_2 = 0.5 * (image_2 + 1.0)
    # Temporally consistent color jittering.
    image_1 = video_ssl_preprocess_ops.random_color_jitter_3d(image_1)
    image_2 = video_ssl_preprocess_ops.random_color_jitter_3d(image_2)
    # Temporally consistent gaussian blurring.
    image_1 = video_ssl_preprocess_ops.random_blur(image_1, crop_size,
                                                   crop_size, 1.0)
    image_2 = video_ssl_preprocess_ops.random_blur(image_2, crop_size,
                                                   crop_size, 0.1)
    image_2 = video_ssl_preprocess_ops.random_solarization(image_2)
    image = tf.concat([image_1, image_2], axis=0)
    image = tf.clip_by_value(image, 0., 1.)
    if zero_centering_image:
      image = 2 * (image - 0.5)

  return image