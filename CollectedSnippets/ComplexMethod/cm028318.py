def build_center_net_meta_arch(build_resnet=False,
                               num_classes=_NUM_CLASSES,
                               max_box_predictions=5,
                               apply_non_max_suppression=False,
                               detection_only=False,
                               per_keypoint_offset=False,
                               predict_depth=False,
                               per_keypoint_depth=False,
                               peak_radius=0,
                               keypoint_only=False,
                               candidate_ranking_mode='min_distance',
                               argmax_postprocessing=False,
                               rescore_instances=False):
  """Builds the CenterNet meta architecture."""
  if build_resnet:
    feature_extractor = (
        center_net_resnet_feature_extractor.CenterNetResnetFeatureExtractor(
            'resnet_v2_101'))
  else:
    feature_extractor = DummyFeatureExtractor(
        channel_means=(1.0, 2.0, 3.0),
        channel_stds=(10., 20., 30.),
        bgr_ordering=False,
        num_feature_outputs=2,
        stride=4)
  image_resizer_fn = functools.partial(
      preprocessor.resize_to_range,
      min_dimension=128,
      max_dimension=128,
      pad_to_max_dimesnion=True)

  non_max_suppression_fn = None
  if apply_non_max_suppression:
    post_processing_proto = post_processing_pb2.PostProcessing()
    post_processing_proto.batch_non_max_suppression.iou_threshold = 0.6
    post_processing_proto.batch_non_max_suppression.score_threshold = 0.6
    (post_processing_proto.batch_non_max_suppression.max_total_detections
    ) = max_box_predictions
    (post_processing_proto.batch_non_max_suppression.max_detections_per_class
    ) = max_box_predictions
    (post_processing_proto.batch_non_max_suppression.change_coordinate_frame
    ) = False
    non_max_suppression_fn, _ = post_processing_builder.build(
        post_processing_proto)

  if keypoint_only:
    num_candidates_per_keypoint = 100 if max_box_predictions > 1 else 1
    return cnma.CenterNetMetaArch(
        is_training=True,
        add_summaries=False,
        num_classes=num_classes,
        feature_extractor=feature_extractor,
        image_resizer_fn=image_resizer_fn,
        object_center_params=get_fake_center_params(max_box_predictions),
        keypoint_params_dict={
            _TASK_NAME:
                get_fake_kp_params(num_candidates_per_keypoint,
                                   per_keypoint_offset, predict_depth,
                                   per_keypoint_depth, peak_radius,
                                   candidate_ranking_mode,
                                   argmax_postprocessing, rescore_instances)
        },
        non_max_suppression_fn=non_max_suppression_fn)
  elif detection_only:
    return cnma.CenterNetMetaArch(
        is_training=True,
        add_summaries=False,
        num_classes=num_classes,
        feature_extractor=feature_extractor,
        image_resizer_fn=image_resizer_fn,
        object_center_params=get_fake_center_params(max_box_predictions),
        object_detection_params=get_fake_od_params(),
        non_max_suppression_fn=non_max_suppression_fn)
  elif num_classes == 1:
    num_candidates_per_keypoint = 100 if max_box_predictions > 1 else 1
    return cnma.CenterNetMetaArch(
        is_training=True,
        add_summaries=False,
        num_classes=num_classes,
        feature_extractor=feature_extractor,
        image_resizer_fn=image_resizer_fn,
        object_center_params=get_fake_center_params(max_box_predictions),
        object_detection_params=get_fake_od_params(),
        keypoint_params_dict={
            _TASK_NAME:
                get_fake_kp_params(num_candidates_per_keypoint,
                                   per_keypoint_offset, predict_depth,
                                   per_keypoint_depth, peak_radius,
                                   candidate_ranking_mode,
                                   argmax_postprocessing, rescore_instances)
        },
        non_max_suppression_fn=non_max_suppression_fn)
  else:
    return cnma.CenterNetMetaArch(
        is_training=True,
        add_summaries=False,
        num_classes=num_classes,
        feature_extractor=feature_extractor,
        image_resizer_fn=image_resizer_fn,
        object_center_params=get_fake_center_params(),
        object_detection_params=get_fake_od_params(),
        keypoint_params_dict={_TASK_NAME: get_fake_kp_params(
            candidate_ranking_mode=candidate_ranking_mode)},
        mask_params=get_fake_mask_params(),
        densepose_params=get_fake_densepose_params(),
        track_params=get_fake_track_params(),
        temporal_offset_params=get_fake_temporal_offset_params(),
        non_max_suppression_fn=non_max_suppression_fn)