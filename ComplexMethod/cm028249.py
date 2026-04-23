def _build_center_net_model(center_net_config, is_training, add_summaries):
  """Build a CenterNet detection model.

  Args:
    center_net_config: A CenterNet proto object with model configuration.
    is_training: True if this model is being built for training purposes.
    add_summaries: Whether to add tf summaries in the model.

  Returns:
    CenterNetMetaArch based on the config.

  """

  image_resizer_fn = image_resizer_builder.build(
      center_net_config.image_resizer)
  _check_feature_extractor_exists(center_net_config.feature_extractor.type)
  feature_extractor = _build_center_net_feature_extractor(
      center_net_config.feature_extractor, is_training)
  object_center_params = object_center_proto_to_params(
      center_net_config.object_center_params)

  object_detection_params = None
  if center_net_config.HasField('object_detection_task'):
    object_detection_params = object_detection_proto_to_params(
        center_net_config.object_detection_task)

  if center_net_config.HasField('deepmac_mask_estimation'):
    logging.warn(('Building experimental DeepMAC meta-arch.'
                  ' Some features may be omitted.'))
    deepmac_params = deepmac_meta_arch.deepmac_proto_to_params(
        center_net_config.deepmac_mask_estimation)
    return deepmac_meta_arch.DeepMACMetaArch(
        is_training=is_training,
        add_summaries=add_summaries,
        num_classes=center_net_config.num_classes,
        feature_extractor=feature_extractor,
        image_resizer_fn=image_resizer_fn,
        object_center_params=object_center_params,
        object_detection_params=object_detection_params,
        deepmac_params=deepmac_params)

  keypoint_params_dict = None
  if center_net_config.keypoint_estimation_task:
    label_map_proto = label_map_util.load_labelmap(
        center_net_config.keypoint_label_map_path)
    keypoint_map_dict = {
        item.name: item for item in label_map_proto.item if item.keypoints
    }
    keypoint_params_dict = {}
    keypoint_class_id_set = set()
    all_keypoint_indices = []
    for task in center_net_config.keypoint_estimation_task:
      kp_params = keypoint_proto_to_params(task, keypoint_map_dict)
      keypoint_params_dict[task.task_name] = kp_params
      all_keypoint_indices.extend(kp_params.keypoint_indices)
      if kp_params.class_id in keypoint_class_id_set:
        raise ValueError(('Multiple keypoint tasks map to the same class id is '
                          'not allowed: %d' % kp_params.class_id))
      else:
        keypoint_class_id_set.add(kp_params.class_id)
    if len(all_keypoint_indices) > len(set(all_keypoint_indices)):
      raise ValueError('Some keypoint indices are used more than once.')

  mask_params = None
  if center_net_config.HasField('mask_estimation_task'):
    mask_params = mask_proto_to_params(center_net_config.mask_estimation_task)

  densepose_params = None
  if center_net_config.HasField('densepose_estimation_task'):
    densepose_params = densepose_proto_to_params(
        center_net_config.densepose_estimation_task)

  track_params = None
  if center_net_config.HasField('track_estimation_task'):
    track_params = tracking_proto_to_params(
        center_net_config.track_estimation_task)

  temporal_offset_params = None
  if center_net_config.HasField('temporal_offset_task'):
    temporal_offset_params = temporal_offset_proto_to_params(
        center_net_config.temporal_offset_task)
  non_max_suppression_fn = None
  if center_net_config.HasField('post_processing'):
    non_max_suppression_fn, _ = post_processing_builder.build(
        center_net_config.post_processing)

  return center_net_meta_arch.CenterNetMetaArch(
      is_training=is_training,
      add_summaries=add_summaries,
      num_classes=center_net_config.num_classes,
      feature_extractor=feature_extractor,
      image_resizer_fn=image_resizer_fn,
      object_center_params=object_center_params,
      object_detection_params=object_detection_params,
      keypoint_params_dict=keypoint_params_dict,
      mask_params=mask_params,
      densepose_params=densepose_params,
      track_params=track_params,
      temporal_offset_params=temporal_offset_params,
      use_depthwise=center_net_config.use_depthwise,
      compute_heatmap_sparse=center_net_config.compute_heatmap_sparse,
      non_max_suppression_fn=non_max_suppression_fn,
      output_prediction_dict=center_net_config.output_prediction_dict)