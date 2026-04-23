def add_image(parser_builder: builders.BaseParserBuilder,
              sampler_builder: builders.SamplerBuilder,
              decoder_builder: builders.DecoderBuilder,
              preprocessor_builder: builders.PreprocessorBuilder,
              postprocessor_builder: builders.PostprocessorBuilder,
              input_feature_name: str = 'image/encoded',
              output_feature_name: str = builders.IMAGE_FEATURE_NAME,
              is_training: bool = True,
              sample_around_keyframe: bool = False,
              sample_from_segments: bool = False,
              # Video related parameters.
              num_frames: int = 32,
              temporal_stride: int = 1,
              num_test_clips: int = 1,
              crop_size: int = 200,
              min_resize: int = 224,
              multi_crop: bool = False,
              zero_centering_image: bool = False,
              random_flip_image: bool = True,
              augmentation_type: str = 'Inception',
              augmentation_params: Optional[Mapping[str, Any]] = None,
              randaug_params: Optional[Mapping[str, Any]] = None,
              autoaug_params: Optional[Mapping[str, Any]] = None,
              sync_random_state: bool = True,
              seed: Optional[int] = None):
  """Adds functions to process image feature to builders.

  Args:
    parser_builder: An instance of a builders.BaseParserBuilder.
    sampler_builder: An instance of a builders.SamplerBuilder.
    decoder_builder: An instance of a builders.DecoderBuilder.
    preprocessor_builder: An instance of a builders.PreprocessorBuilder.
    postprocessor_builder: An instance of a builders.PostprocessorBuilder.
    input_feature_name: Name of the feature in the input SequenceExample.
      Exposing this as an argument allows using this function for different
      image features.
    output_feature_name: Name of the feature in the output features dictionary.
      Exposing this as an argument allows using this function for different
      image features.
    is_training: Whether or not perform random operations. If True, random
      sample, crop and left right flip is used.
    sample_around_keyframe: Whether to sample clip around the keyframe. If True,
      the random temporal sampling will be overridden and disabled.
    sample_from_segments: Whether to sample frames from segments of a video. If
      True, the temporal_stride will be ignored.
    num_frames: Number of frames per subclip.
    temporal_stride: Temporal stride to sample frames.
    num_test_clips: Number of test clips (1 by default). If more than 1, this
      will sample multiple linearly spaced clips within each video at test time.
      If 1, then a single clip in the middle of the video is sampled. The clips
      are aggreagated in the batch dimension.
    crop_size: Final size of the frame after cropping the resized frames. Both
      height and width are the same.
    min_resize: The minimal length resize before cropping.
    multi_crop: Whether to perform 3-view crop or not. This is only enabled
      in evaluation mode. If is_training=True, this is ignored.
    zero_centering_image: If True, frames are normalized to values in [-1, 1].
      If False, values in [0, 1].
    random_flip_image: If True, frames are randomly horizontal flipped during
      the training.
    augmentation_type: The style of Crop+Resize procedure. Support options:
      ['Inception', 'VGG'].
    augmentation_params: A dictionary contains image augmentation parameters
      associated with the augmentation style.
    randaug_params: A dictionary of params for RandAug policy.
    autoaug_params:  A dictionary of params for AutoAug policy.
    sync_random_state: Whether to use stateful option to keep random operations
      in sync between different modalities. All modalities having this option
      True will use the same outcome in random operations such as sampling and
      cropping.
    seed: the random seed.
  """
  # Validate parameters.
  if sync_random_state and multi_crop:
    raise ValueError('multi_crop is not supported with sync random states.')

  if augmentation_type.lower() == 'ava' and multi_crop:
    raise ValueError('multi_crop should not be combined with ava augmentation.')

  if sample_from_segments and sample_around_keyframe:
    raise ValueError('sample_from_segments and sample_around_keyframes cannot '
                     'be True at the same time.')

  if sample_from_segments and num_test_clips > 1:
    raise ValueError(
        'sample_from_segments is set to True while got num_test_clips: %d'
        % num_test_clips
    )

  # Parse frames.
  if isinstance(parser_builder, builders.SequenceExampleParserBuilder):
    parser_builder.parse_feature(
        feature_name=input_feature_name,
        feature_type=tf.io.FixedLenSequenceFeature((), dtype=tf.string),
        output_name=output_feature_name)
  elif isinstance(parser_builder, builders.ExampleParserBuilder):
    parser_builder.parse_feature(
        feature_name=input_feature_name,
        feature_type=tf.io.FixedLenFeature((), dtype=tf.string),
        output_name=output_feature_name)
    sampler_builder.add_fn(
        fn=lambda x: tf.expand_dims(x, axis=0),
        feature_name=output_feature_name,
        fn_name=f'{output_feature_name}_expand_dim')
  else:
    raise ValueError('`parser_builder` has an unexpected type.')

  if sample_around_keyframe:
    # Sample clip around keyframe.
    sample_around_keyframe_fn = functools.partial(
        processors.sample_sequence_around_keyframe,
        num_steps=num_frames,
        stride=temporal_stride,
        sample_target_key=output_feature_name)
    sampler_builder.add_fn(
        fn=sample_around_keyframe_fn,
        fn_name='{}_sample_around_keyframe'.format(output_feature_name))
  elif sample_from_segments:
    sample_segment_fn = functools.partial(
        processors.sample_sequence_by_segment,
        num_steps=num_frames,
        sample_target_key=output_feature_name,
        is_training=is_training)
    sampler_builder.add_fn(
        fn=sample_segment_fn,
        fn_name='{}_segment_sample'.format(output_feature_name))
  elif is_training:
    # Sample random clip.
    def sample_sequence_fn(x, state):
      return processors.sample_sequence(
          x,
          num_steps=num_frames, random=True, stride=temporal_stride, seed=seed,
          state=state)
    sampler_builder.add_fn(
        fn=sample_sequence_fn,
        feature_name=output_feature_name,
        fn_name='{}_random_sample'.format(output_feature_name),
        stateful=sync_random_state)
  else:
    if num_test_clips > 1:
      sample_linespace_sequence_fn = functools.partial(
          processors.sample_linsapce_sequence,
          num_windows=num_test_clips,
          num_steps=num_frames,
          stride=temporal_stride)
      # Sample linspace clips.
      sampler_builder.add_fn(
          fn=sample_linespace_sequence_fn,
          feature_name=output_feature_name,
          fn_name='{}_linspace_sample'.format(output_feature_name))
    else:
      sample_sequence_fn = functools.partial(
          processors.sample_sequence,
          num_steps=num_frames, random=False, stride=temporal_stride, seed=None)
      # Sample middle clip.
      sampler_builder.add_fn(
          fn=sample_sequence_fn,
          feature_name=output_feature_name,
          fn_name='{}_middle_sample'.format(output_feature_name))

  # Decode JPEG string to tf.uint8.
  num_raw_channels = 3
  decoder_builder.add_fn(
      fn=lambda x: processors.decode_jpeg(x, channels=num_raw_channels),
      feature_name=output_feature_name,
      fn_name='{}_decode_jpeg'.format(output_feature_name))

  # Image crop, resize or pad.
  if is_training:
    if augmentation_type.lower() == 'inception':
      min_aspect_ratio = augmentation_params['min_aspect_ratio']
      max_aspect_ratio = augmentation_params['max_aspect_ratio']
      min_area_ratio = augmentation_params['min_area_ratio']
      max_area_ratio = augmentation_params['max_area_ratio']
      # Inception-style image crop: random crop -> resize.
      def random_crop_resize_fn(x, state=None):
        return processors.random_crop_resize(
            x, output_height=crop_size, output_width=crop_size,
            num_frames=num_frames, num_channels=num_raw_channels,
            aspect_ratio=(min_aspect_ratio, max_aspect_ratio),
            area_range=(min_area_ratio, max_area_ratio),
            state=state)
      preprocessor_builder.add_fn(
          fn=random_crop_resize_fn,
          feature_name=output_feature_name,
          fn_name='{}_random_crop_resize'.format(output_feature_name),
          stateful=sync_random_state)
    elif augmentation_type.lower() == 'vgg':
      # VGG-style image crop: resize -> random crop.
      def resize_and_crop_fn(x, state):
        return processors.resize_and_crop(
            x,
            min_resize=min_resize,
            crop_size=crop_size, is_flow=False, is_random=True,
            state=state)
      preprocessor_builder.add_fn(
          fn=resize_and_crop_fn,
          feature_name=output_feature_name,
          fn_name='{}_resize_random_crop'.format(output_feature_name),
          stateful=sync_random_state)
    elif augmentation_type.lower() == 'ava':
      # AVA-style image aug: random_crop -> resize -> random pad.
      def random_square_crop_by_scale_fn(x, state=None):
        return processors.random_square_crop_by_scale(
            image=x,
            scale_min=augmentation_params['scale_min'],
            scale_max=augmentation_params['scale_max'],
            state=state)
      preprocessor_builder.add_fn(
          fn=random_square_crop_by_scale_fn,
          feature_name=output_feature_name,
          fn_name='{}_random_square_crop_by_scale'.format(output_feature_name),
          stateful=sync_random_state)
      def resize_and_pad_fn(x, state=None):
        return processors.resize_and_pad(
            frames=x,
            max_resize=crop_size,
            pad_size=crop_size,
            random=True,
            state=state)
      preprocessor_builder.add_fn(
          fn=resize_and_pad_fn,
          feature_name=output_feature_name,
          fn_name='{}_resize_random_pad'.format(output_feature_name),
          # Use state to keep coherence between modalities if requested.
          stateful=sync_random_state)
    else:
      raise ValueError('Unrecognized augmentation_type: %s' %
                       augmentation_type)

    if random_flip_image:
      def random_flip_left_right_fn(x, state=None):
        return processors.random_flip_left_right(
            x, seed=seed, is_flow=False, state=state)
      preprocessor_builder.add_fn(
          fn=random_flip_left_right_fn,
          feature_name=output_feature_name,
          fn_name='{}_random_flip'.format(output_feature_name),
          stateful=sync_random_state)
  else:
    # Crop images, either a 3-view crop or a central crop.
    if multi_crop:
      resize_smallest_fn = functools.partial(
          processors.resize_smallest,
          min_resize=min_resize,
          is_flow=False)
      # Resize images (resize happens only if necessary to save compute).
      preprocessor_builder.add_fn(
          fn=resize_smallest_fn,
          feature_name=output_feature_name,
          fn_name='{}_resize_smallest'.format(output_feature_name))
      # Multi crop of the frames.
      preprocessor_builder.add_fn(
          fn=lambda x: processors.multi_crop_image(x, crop_size, crop_size),
          feature_name=output_feature_name,
          fn_name='{}_multi_crop'.format(output_feature_name))
    else:
      if augmentation_type.lower() == 'ava':
        def resize_and_pad_fn(x, state=None):
          return processors.resize_and_pad(
              frames=x,
              max_resize=crop_size,
              pad_size=crop_size,
              random=False,
              state=state)
        preprocessor_builder.add_fn(
            fn=resize_and_pad_fn,
            feature_name=output_feature_name,
            fn_name='{}_resize_central_pad'.format(output_feature_name),
            stateful=sync_random_state)
      else:
        def resize_and_crop_fn(x, state=None):
          return processors.resize_and_crop(
              x,
              min_resize=min_resize,
              crop_size=crop_size,
              is_flow=False,
              is_random=False,
              state=state)
        preprocessor_builder.add_fn(
            fn=resize_and_crop_fn,
            feature_name=output_feature_name,
            fn_name='{}_resize_central_crop'.format(output_feature_name),
            stateful=sync_random_state)

  # Apply extra augmentation policy.
  if is_training:
    if randaug_params is not None and autoaug_params is not None:
      raise ValueError('Choose to apply one of data augmentation policies: '
                       'randaug and autoaug.')

    if autoaug_params is not None:
      augmenter = augment.AutoAugment(
          augmentation_name=autoaug_params['augmentation_name'],
          cutout_const=autoaug_params['cutout_const'],
          translate_const=autoaug_params['translate_const'])
      preprocessor_builder.add_fn(
          fn=augmenter.distort,
          feature_name=output_feature_name,
          fn_name='{}_autoaug'.format(output_feature_name))

    if randaug_params is not None:
      augmenter = augment.RandAugment(
          num_layers=randaug_params['num_layers'],
          magnitude=randaug_params['magnitude'],
          cutout_const=randaug_params['cutout_const'],
          translate_const=randaug_params['translate_const'],
          prob_to_apply=randaug_params['prob_to_apply'],
          exclude_ops=randaug_params['exclude_ops'])
      preprocessor_builder.add_fn(
          fn=augmenter.distort,
          feature_name=output_feature_name,
          fn_name='{}_randaug'.format(output_feature_name))

  # Cast the frames in float32, normalizing according to zero_centering_image.
  preprocessor_builder.add_fn(
      fn=lambda x: processors.normalize_image(x, zero_centering_image),
      feature_name=output_feature_name,
      fn_name='{}_normalize'.format(output_feature_name))

  if (num_test_clips > 1 or multi_crop) and not is_training:
    # In this case, multiple clips are merged together in batch dimenstion which
    # will be B * num_test_clips.
    def reshape_fn(x):
      target_shape = (-1, num_frames, x.shape[-3], x.shape[-2], x.shape[-1])
      return tf.reshape(x, target_shape)
    postprocessor_builder.add_fn(
        fn=reshape_fn,
        feature_name=output_feature_name,
        fn_name='{}_reshape'.format(output_feature_name))