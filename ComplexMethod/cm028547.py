def _build(self,
             is_training: bool = True,
             # Video related parameters.
             num_frames: int = 32,
             temporal_stride: int = 1,
             num_instance_per_frame: int = 5,
             # Image related parameters.
             min_resize: int = 224,
             crop_size: int = 200,
             zero_centering_image: bool = False,
             color_augmentation: bool = False,
             augmentation_type: str = 'AVA',
             augmentation_params: Optional[Mapping[str, Any]] = None,
             # Test related parameters,
             num_test_clips: int = 1,
             # Label related parameters.
             one_hot_label: bool = True,
             merge_multi_labels: bool = False,
             import_detected_bboxes: bool = False):
    """Builds the data processing graph.

    Args:
      is_training: Whether or not in training mode. If `True`, random sample,
        crop and left right flip are used.
      num_frames: Number of frames per subclip.
      temporal_stride: Temporal stride to sample frames.
      num_instance_per_frame: The max number of instances per frame to keep.
      min_resize: Frames are resized so that `min(height, width)` is
        `min_resize`.
      crop_size: Final size of the frame after cropping the resized frames. Both
        height and width are the same.
      zero_centering_image: If `True`, frames are normalized to values in
        [-1, 1]. If `False`, values in [0, 1].
      color_augmentation: Whether to apply color augmentation on video clips.
      augmentation_type: The data augmentation style applied on images.
      augmentation_params: A dictionary of params for data augmentation.
      num_test_clips: Number of test clips (1 by default). If more than 1, this
        will sample multiple linearly spaced clips within each video at test
        time. If 1, then a single clip in the middle of the video is sampled.
        The clips are aggreagated in the batch dimension.
      one_hot_label: Whether to return one-hot label.
      merge_multi_labels: Whether to merge multi_labels.
      import_detected_bboxes: Whether to parse and return detected boxes.
    """
    if num_test_clips != 1:
      raise ValueError('only support num_test_clips = 1 for action '
                       'localization task. ')

    # Parse keyframe index.
    self.parser_builder.parse_feature(
        feature_type=tf.io.FixedLenFeature(1, dtype=tf.int64),
        feature_name=self._KEYFRAME_INDEX_KEY,
        output_name='keyframe_index',
        is_context=True)
    # Add keyframe boxes.
    for dim in ['ymin', 'xmin', 'ymax', 'xmax']:
      utils.add_context_box_dim(
          parser_builder=self.parser_builder,
          sampler_builder=self.sampler_builder,
          preprocessor_builder=self.preprocessor_builder,
          input_box_dim_name=f'{self._GT_PREFIX}/bbox/{dim}',
          output_box_dim_name=f'instances_{dim}',
          num_instances_per_frame=num_instance_per_frame,
          num_frames=num_frames)   # > 1 to duplicate keyframe boxes to all.
    utils.group_instance_box_dims(
        preprocessor_builder=self.preprocessor_builder,
        output_position_name='instances_position',
        box_key_prefix='instances')
    # Add boxes scores
    utils.add_context_box_dim(
        parser_builder=self.parser_builder,
        sampler_builder=self.sampler_builder,
        preprocessor_builder=self.preprocessor_builder,
        input_box_dim_name=f'{self._GT_PREFIX}/bbox/score',
        output_box_dim_name='instances_score',
        num_instances_per_frame=num_instance_per_frame,
        num_frames=num_frames,   # duplicate keyframe boxes to all frames.
        default_value=1.0)
    if is_training:
      filter_instances_position_by_score_fn = functools.partial(
          utils.filter_instances_box_by_score,
          box_key_prefix='instances',
          score_threshold=self._TRAIN_DETECTION_SCORE)
      self.preprocessor_builder.add_fn(
          fn=filter_instances_position_by_score_fn,
          fn_name='filter_training_boxes')
    else:
      self.preprocessor_builder.add_fn(
          fn=lambda x: utils.infer_instances_mask_from_position(inputs=x),
          fn_name='infer_instances_mask')

    # Add detected boxes.
    if (not is_training) and import_detected_bboxes:
      for dim in ['ymin', 'xmin', 'ymax', 'xmax', 'score']:
        utils.add_instance_box_dim(
            parser_builder=self.parser_builder,
            sampler_builder=self.sampler_builder,
            preprocessor_builder=self.preprocessor_builder,
            input_box_dim_name='{}/bbox/{}'.format(self._DETECTOR_PREFIX, dim),
            output_box_dim_name='detected_instances_{}'.format(dim),
            sample_around_keyframe=True,
            sample_random=False,
            num_instances_per_frame=num_instance_per_frame,
            num_frames=num_frames,
            temporal_stride=temporal_stride,
            sync_random_state=True)
      utils.group_instance_box_dims(
          preprocessor_builder=self.preprocessor_builder,
          box_key_prefix='detected_instances',
          output_position_name='detected_instances_position')
      filter_instances_position_by_score_fn = functools.partial(
          utils.filter_instances_box_by_score,
          box_key_prefix='detected_instances',
          score_threshold=self._EVAL_DETECTION_SCORE)
      self.preprocessor_builder.add_fn(
          fn=filter_instances_position_by_score_fn,
          fn_name='filter_detected_boxes')

    # Add images.
    utils.add_image(
        parser_builder=self.parser_builder,
        sampler_builder=self.sampler_builder,
        decoder_builder=self.decoder_builder,
        preprocessor_builder=self.preprocessor_builder,
        postprocessor_builder=self.postprocessor_builder,
        sample_around_keyframe=True,
        is_training=is_training,
        num_frames=num_frames,
        temporal_stride=temporal_stride,
        num_test_clips=num_test_clips,
        crop_size=crop_size,
        min_resize=min_resize,
        multi_crop=False,
        zero_centering_image=zero_centering_image,
        augmentation_type=augmentation_type,
        augmentation_params=augmentation_params,
        sync_random_state=True)

    # Adapt boxes to the image augmentations.
    utils.adjust_positions(
        preprocessor_builder=self.preprocessor_builder,
        input_tensor_name='instances_position',
        output_tensor_name='instances_position')
    if import_detected_bboxes:
      utils.adjust_positions(
          preprocessor_builder=self.preprocessor_builder,
          input_tensor_name='detected_instances_position',
          output_tensor_name='detected_instances_position')

    utils.add_context_label(
        parser_builder=self.parser_builder,
        sampler_builder=self.sampler_builder,
        preprocessor_builder=self.preprocessor_builder,
        input_label_index_feature_name=f'{self._GT_PREFIX}/bbox/label/index',
        input_label_name_feature_name=f'{self._GT_PREFIX}/bbox/label/string',
        num_instances_per_frame=num_instance_per_frame,
        num_frames=num_frames,
        zero_based_index=self._ZERO_BASED_INDEX,
        # merge_multi_labels fn expects label in 0-index id.
        one_hot_label=False if merge_multi_labels else one_hot_label,
        num_classes=self._NUM_CLASSES,
        add_label_name=False)
    if merge_multi_labels:
      self.preprocessor_builder.add_fn(
          fn=functools.partial(
              utils.merge_multi_labels,
              num_classes=self._NUM_CLASSES),
          fn_name='merge_multi_labels')

    if is_training and color_augmentation:
      utils.apply_default_color_augmentations(
          preprocessor_builder=self.preprocessor_builder,
          zero_centering_image=zero_centering_image)

    self.postprocessor_builder.add_fn(
        fn=utils.update_valid_instances_mask,
        fn_name='update_valid_instances_mask')

    select_keyframe_instances_fn = functools.partial(
        self._select_keyframe_instances,
        keyframe_index=(num_frames // 2),
        import_detected_bboxes=import_detected_bboxes)
    self.postprocessor_builder.add_fn(
        fn=select_keyframe_instances_fn,
        fn_name='slice_keyframe_instances')