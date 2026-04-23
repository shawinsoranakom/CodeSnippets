def eval_input(eval_config, eval_input_config, model_config,
               model=None, params=None, input_context=None):
  """Returns `features` and `labels` tensor dictionaries for evaluation.

  Args:
    eval_config: An eval_pb2.EvalConfig.
    eval_input_config: An input_reader_pb2.InputReader.
    model_config: A model_pb2.DetectionModel.
    model: A pre-constructed Detection Model.
      If None, one will be created from the config.
    params: Parameter dictionary passed from the estimator.
    input_context: optional, A tf.distribute.InputContext object used to
      shard filenames and compute per-replica batch_size when this function
      is being called per-replica.

  Returns:
    A tf.data.Dataset that holds (features, labels) tuple.

    features: Dictionary of feature tensors.
      features[fields.InputDataFields.image] is a [1, H, W, C] float32 tensor
        with preprocessed images.
      features[HASH_KEY] is a [1] int32 tensor representing unique
        identifiers for the images.
      features[fields.InputDataFields.true_image_shape] is a [1, 3]
        int32 tensor representing the true image shapes, as preprocessed
        images could be padded.
      features[fields.InputDataFields.original_image] is a [1, H', W', C]
        float32 tensor with the original image.
    labels: Dictionary of groundtruth tensors.
      labels[fields.InputDataFields.groundtruth_boxes] is a [1, num_boxes, 4]
        float32 tensor containing the corners of the groundtruth boxes.
      labels[fields.InputDataFields.groundtruth_classes] is a
        [num_boxes, num_classes] float32 one-hot tensor of classes.
      labels[fields.InputDataFields.groundtruth_area] is a [1, num_boxes]
        float32 tensor containing object areas.
      labels[fields.InputDataFields.groundtruth_is_crowd] is a [1, num_boxes]
        bool tensor indicating if the boxes enclose a crowd.
      labels[fields.InputDataFields.groundtruth_difficult] is a [1, num_boxes]
        int32 tensor indicating if the boxes represent difficult instances.
      -- Optional --
      labels[fields.InputDataFields.groundtruth_instance_masks] is a
        [1, num_boxes, H, W] float32 tensor containing only binary values,
        which represent instance masks for objects.
      labels[fields.InputDataFields.groundtruth_instance_mask_weights] is a
        [1, num_boxes] float32 tensor containing groundtruth weights for each
        instance mask.
      labels[fields.InputDataFields.groundtruth_weights] is a
        [batch_size, num_boxes, num_keypoints] float32 tensor containing
        groundtruth weights for the keypoints.
      labels[fields.InputDataFields.groundtruth_visibilities] is a
        [batch_size, num_boxes, num_keypoints] bool tensor containing
        groundtruth visibilities for each keypoint.
      labels[fields.InputDataFields.groundtruth_group_of] is a [1, num_boxes]
        bool tensor indicating if the box covers more than 5 instances of the
        same class which heavily occlude each other.
      labels[fields.InputDataFields.groundtruth_labeled_classes] is a
        [num_boxes, num_classes] float32 k-hot tensor of classes.
      labels[fields.InputDataFields.groundtruth_dp_num_points] is a
        [batch_size, num_boxes] int32 tensor with the number of sampled
        DensePose points per object.
      labels[fields.InputDataFields.groundtruth_dp_part_ids] is a
        [batch_size, num_boxes, max_sampled_points] int32 tensor with the
        DensePose part ids (0-indexed) per object.
      labels[fields.InputDataFields.groundtruth_dp_surface_coords] is a
        [batch_size, num_boxes, max_sampled_points, 4] float32 tensor with the
        DensePose surface coordinates. The format is (y, x, v, u), where (y, x)
        are normalized image coordinates and (v, u) are normalized surface part
        coordinates.
      labels[fields.InputDataFields.groundtruth_track_ids] is a
        [batch_size, num_boxes] int32 tensor with the track ID for each object.

  Raises:
    TypeError: if the `eval_config`, `eval_input_config` or `model_config`
      are not of the correct type.
  """
  params = params or {}
  if not isinstance(eval_config, eval_pb2.EvalConfig):
    raise TypeError('For eval mode, the `eval_config` must be a '
                    'train_pb2.EvalConfig.')
  if not isinstance(eval_input_config, input_reader_pb2.InputReader):
    raise TypeError('The `eval_input_config` must be a '
                    'input_reader_pb2.InputReader.')
  if not isinstance(model_config, model_pb2.DetectionModel):
    raise TypeError('The `model_config` must be a '
                    'model_pb2.DetectionModel.')

  if eval_config.force_no_resize:
    arch = model_config.WhichOneof('model')
    arch_config = getattr(model_config, arch)
    image_resizer_proto = image_resizer_pb2.ImageResizer()
    image_resizer_proto.identity_resizer.CopyFrom(
        image_resizer_pb2.IdentityResizer())
    arch_config.image_resizer.CopyFrom(image_resizer_proto)

  if model is None:
    model_preprocess_fn = INPUT_BUILDER_UTIL_MAP['model_build'](
        model_config, is_training=False).preprocess
  else:
    model_preprocess_fn = model.preprocess

  def transform_and_pad_input_data_fn(tensor_dict):
    """Combines transform and pad operation."""
    num_classes = config_util.get_number_of_classes(model_config)

    image_resizer_config = config_util.get_image_resizer_config(model_config)
    image_resizer_fn = image_resizer_builder.build(image_resizer_config)
    keypoint_type_weight = eval_input_config.keypoint_type_weight or None

    transform_data_fn = functools.partial(
        transform_input_data, model_preprocess_fn=model_preprocess_fn,
        image_resizer_fn=image_resizer_fn,
        num_classes=num_classes,
        data_augmentation_fn=None,
        retain_original_image=eval_config.retain_original_images,
        retain_original_image_additional_channels=
        eval_config.retain_original_image_additional_channels,
        keypoint_type_weight=keypoint_type_weight,
        image_classes_field_map_empty_to_ones=eval_config
        .image_classes_field_map_empty_to_ones)
    tensor_dict = pad_input_data_to_static_shapes(
        tensor_dict=transform_data_fn(tensor_dict),
        max_num_boxes=eval_input_config.max_number_of_boxes,
        num_classes=config_util.get_number_of_classes(model_config),
        spatial_image_shape=config_util.get_spatial_image_size(
            image_resizer_config),
        max_num_context_features=config_util.get_max_num_context_features(
            model_config),
        context_feature_length=config_util.get_context_feature_length(
            model_config))
    include_source_id = eval_input_config.include_source_id
    return (_get_features_dict(tensor_dict, include_source_id),
            _get_labels_dict(tensor_dict))

  reduce_to_frame_fn = get_reduce_to_frame_fn(eval_input_config, False)

  dataset = INPUT_BUILDER_UTIL_MAP['dataset_build'](
      eval_input_config,
      batch_size=params['batch_size'] if params else eval_config.batch_size,
      transform_input_data_fn=transform_and_pad_input_data_fn,
      input_context=input_context,
      reduce_to_frame_fn=reduce_to_frame_fn)
  return dataset