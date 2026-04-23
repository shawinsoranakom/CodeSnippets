def keypoint_proto_to_params(kp_config, keypoint_map_dict):
  """Converts CenterNet.KeypointEstimation proto to parameter namedtuple."""
  label_map_item = keypoint_map_dict[kp_config.keypoint_class_name]

  classification_loss, localization_loss, _, _, _, _, _ = (
      losses_builder.build(kp_config.loss))

  keypoint_indices = [
      keypoint.id for keypoint in label_map_item.keypoints
  ]
  keypoint_labels = [
      keypoint.label for keypoint in label_map_item.keypoints
  ]
  keypoint_std_dev_dict = {
      label: KEYPOINT_STD_DEV_DEFAULT for label in keypoint_labels
  }
  if kp_config.keypoint_label_to_std:
    for label, value in kp_config.keypoint_label_to_std.items():
      keypoint_std_dev_dict[label] = value
  keypoint_std_dev = [keypoint_std_dev_dict[label] for label in keypoint_labels]
  if kp_config.HasField('heatmap_head_params'):
    heatmap_head_num_filters = list(kp_config.heatmap_head_params.num_filters)
    heatmap_head_kernel_sizes = list(kp_config.heatmap_head_params.kernel_sizes)
  else:
    heatmap_head_num_filters = [256]
    heatmap_head_kernel_sizes = [3]
  if kp_config.HasField('offset_head_params'):
    offset_head_num_filters = list(kp_config.offset_head_params.num_filters)
    offset_head_kernel_sizes = list(kp_config.offset_head_params.kernel_sizes)
  else:
    offset_head_num_filters = [256]
    offset_head_kernel_sizes = [3]
  if kp_config.HasField('regress_head_params'):
    regress_head_num_filters = list(kp_config.regress_head_params.num_filters)
    regress_head_kernel_sizes = list(
        kp_config.regress_head_params.kernel_sizes)
  else:
    regress_head_num_filters = [256]
    regress_head_kernel_sizes = [3]
  return center_net_meta_arch.KeypointEstimationParams(
      task_name=kp_config.task_name,
      class_id=label_map_item.id - CLASS_ID_OFFSET,
      keypoint_indices=keypoint_indices,
      classification_loss=classification_loss,
      localization_loss=localization_loss,
      keypoint_labels=keypoint_labels,
      keypoint_std_dev=keypoint_std_dev,
      task_loss_weight=kp_config.task_loss_weight,
      keypoint_regression_loss_weight=kp_config.keypoint_regression_loss_weight,
      keypoint_heatmap_loss_weight=kp_config.keypoint_heatmap_loss_weight,
      keypoint_offset_loss_weight=kp_config.keypoint_offset_loss_weight,
      heatmap_bias_init=kp_config.heatmap_bias_init,
      keypoint_candidate_score_threshold=(
          kp_config.keypoint_candidate_score_threshold),
      num_candidates_per_keypoint=kp_config.num_candidates_per_keypoint,
      peak_max_pool_kernel_size=kp_config.peak_max_pool_kernel_size,
      unmatched_keypoint_score=kp_config.unmatched_keypoint_score,
      box_scale=kp_config.box_scale,
      candidate_search_scale=kp_config.candidate_search_scale,
      candidate_ranking_mode=kp_config.candidate_ranking_mode,
      offset_peak_radius=kp_config.offset_peak_radius,
      per_keypoint_offset=kp_config.per_keypoint_offset,
      predict_depth=kp_config.predict_depth,
      per_keypoint_depth=kp_config.per_keypoint_depth,
      keypoint_depth_loss_weight=kp_config.keypoint_depth_loss_weight,
      score_distance_offset=kp_config.score_distance_offset,
      clip_out_of_frame_keypoints=kp_config.clip_out_of_frame_keypoints,
      rescore_instances=kp_config.rescore_instances,
      heatmap_head_num_filters=heatmap_head_num_filters,
      heatmap_head_kernel_sizes=heatmap_head_kernel_sizes,
      offset_head_num_filters=offset_head_num_filters,
      offset_head_kernel_sizes=offset_head_kernel_sizes,
      regress_head_num_filters=regress_head_num_filters,
      regress_head_kernel_sizes=regress_head_kernel_sizes,
      score_distance_multiplier=kp_config.score_distance_multiplier,
      std_dev_multiplier=kp_config.std_dev_multiplier,
      rescoring_threshold=kp_config.rescoring_threshold,
      gaussian_denom_ratio=kp_config.gaussian_denom_ratio,
      argmax_postprocessing=kp_config.argmax_postprocessing)