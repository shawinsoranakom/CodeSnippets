def process_image(image: tf.Tensor,
                  is_training: bool = True,
                  num_frames: int = 32,
                  stride: int = 1,
                  random_stride_range: int = 0,
                  num_test_clips: int = 1,
                  min_resize: int = 256,
                  crop_size: Union[int, Tuple[int, int]] = 224,
                  num_channels: int = 3,
                  num_crops: int = 1,
                  zero_centering_image: bool = False,
                  min_aspect_ratio: float = 0.5,
                  max_aspect_ratio: float = 2,
                  min_area_ratio: float = 0.49,
                  max_area_ratio: float = 1.0,
                  random_rotation: bool = False,
                  augmenter: Optional[augment.ImageAugment] = None,
                  seed: Optional[int] = None,
                  input_image_format: Optional[str] = 'jpeg') -> tf.Tensor:
  """Processes a serialized image tensor.

  Args:
    image: Input Tensor of shape [time-steps] and type tf.string of serialized
      frames.
    is_training: Whether or not in training mode. If True, random sample, crop
      and left right flip is used.
    num_frames: Number of frames per sub clip.
    stride: Temporal stride to sample frames.
    random_stride_range: An int indicating the min and max bounds to uniformly
      sample different strides from the video. E.g., a value of 1 with stride=2
      will uniformly sample a stride in {1, 2, 3} for each video in a batch.
      Only used enabled training for the purposes of frame-rate augmentation.
      Defaults to 0, which disables random sampling.
    num_test_clips: Number of test clips (1 by default). If more than 1, this
      will sample multiple linearly spaced clips within each video at test time.
      If 1, then a single clip in the middle of the video is sampled. The clips
      are aggregated in the batch dimension.
    min_resize: Frames are resized so that min(height, width) is min_resize.
    crop_size: Final size of the frame after cropping the resized frames.
      Optionally, specify a tuple of (crop_height, crop_width) if
      crop_height != crop_width.
    num_channels: Number of channels of the clip.
    num_crops: Number of crops to perform on the resized frames.
    zero_centering_image: If True, frames are normalized to values in [-1, 1].
      If False, values in [0, 1].
    min_aspect_ratio: The minimum aspect range for cropping.
    max_aspect_ratio: The maximum aspect range for cropping.
    min_area_ratio: The minimum area range for cropping.
    max_area_ratio: The maximum area range for cropping.
    random_rotation: Use uniform random rotation augmentation or not.
    augmenter: Image augmenter to distort each image.
    seed: A deterministic seed to use when sampling.
    input_image_format: The format of input image which could be jpeg, png or
      none for unknown or mixed datasets.

  Returns:
    Processed frames. Tensor of shape
      [num_frames * num_test_clips, crop_height, crop_width, num_channels].
  """
  # Validate parameters.
  if is_training and num_test_clips != 1:
    logging.warning(
        '`num_test_clips` %d is ignored since `is_training` is `True`.',
        num_test_clips)

  if random_stride_range < 0:
    raise ValueError('Random stride range should be >= 0, got {}'.format(
        random_stride_range))

  if input_image_format not in ('jpeg', 'png', 'none'):
    raise ValueError('Unknown input image format: {}'.format(
        input_image_format))

  if isinstance(crop_size, int):
    crop_size = (crop_size, crop_size)
  crop_height, crop_width = crop_size

  # Temporal sampler.
  if is_training:
    if random_stride_range > 0:
      # Uniformly sample different frame-rates
      stride = tf.random.uniform(
          [],
          tf.maximum(stride - random_stride_range, 1),
          stride + random_stride_range,
          dtype=tf.int32)

    # Sample random clip.
    image = preprocess_ops_3d.sample_sequence(image, num_frames, True, stride,
                                              seed)
  elif num_test_clips > 1:
    # Sample linspace clips.
    image = preprocess_ops_3d.sample_linspace_sequence(image, num_test_clips,
                                                       num_frames, stride)
  else:
    # Sample middle clip.
    image = preprocess_ops_3d.sample_sequence(image, num_frames, False, stride)

  # Decode JPEG string to tf.uint8.
  if image.dtype == tf.string:
    image = preprocess_ops_3d.decode_image(image, num_channels)

  if is_training:
    # Standard image data augmentation: random resized crop and random flip.
    image = preprocess_ops_3d.random_crop_resize(
        image, crop_height, crop_width, num_frames, num_channels,
        (min_aspect_ratio, max_aspect_ratio),
        (min_area_ratio, max_area_ratio))
    image = preprocess_ops_3d.random_flip_left_right(image, seed)
    if random_rotation:
      image = preprocess_ops_3d.random_rotation(image, seed)

    if augmenter is not None:
      image = augmenter.distort(image)
  else:
    # Resize images (resize happens only if necessary to save compute).
    image = preprocess_ops_3d.resize_smallest(image, min_resize)
    # Crop of the frames.
    image = preprocess_ops_3d.crop_image(image, crop_height, crop_width, False,
                                         num_crops)

  # Cast the frames in float32, normalizing according to zero_centering_image.
  return preprocess_ops_3d.normalize_image(image, zero_centering_image)