def _build_model(self,
                   is_training,
                   number_of_stages,
                   second_stage_batch_size,
                   first_stage_max_proposals=8,
                   num_classes=2,
                   hard_mining=False,
                   softmax_second_stage_classification_loss=True,
                   predict_masks=False,
                   pad_to_max_dimension=None,
                   masks_are_class_agnostic=False,
                   use_matmul_crop_and_resize=False,
                   clip_anchors_to_image=False,
                   use_matmul_gather_in_matcher=False,
                   use_static_shapes=False,
                   calibration_mapping_value=None,
                   share_box_across_classes=False,
                   return_raw_detections_during_predict=False,
                   output_final_box_features=False,
                   multi_level=False):
    use_keras = tf_version.is_tf2()
    def image_resizer_fn(image, masks=None):
      """Fake image resizer function."""
      resized_inputs = []
      resized_image = tf.identity(image)
      if pad_to_max_dimension is not None:
        resized_image = tf.image.pad_to_bounding_box(image, 0, 0,
                                                     pad_to_max_dimension,
                                                     pad_to_max_dimension)
      resized_inputs.append(resized_image)
      if masks is not None:
        resized_masks = tf.identity(masks)
        if pad_to_max_dimension is not None:
          resized_masks = tf.image.pad_to_bounding_box(tf.transpose(masks,
                                                                    [1, 2, 0]),
                                                       0, 0,
                                                       pad_to_max_dimension,
                                                       pad_to_max_dimension)
          resized_masks = tf.transpose(resized_masks, [2, 0, 1])
        resized_inputs.append(resized_masks)
      resized_inputs.append(tf.shape(image))
      return resized_inputs

    # anchors in this test are designed so that a subset of anchors are inside
    # the image and a subset of anchors are outside.
    first_stage_anchor_generator = None
    if multi_level:
      min_level = 0
      max_level = 1
      anchor_scale = 0.1
      aspect_ratios = [1.0, 2.0, 0.5]
      scales_per_octave = 2
      normalize_coordinates = False
      (first_stage_anchor_generator
      ) = multiscale_grid_anchor_generator.MultiscaleGridAnchorGenerator(
          min_level, max_level, anchor_scale, aspect_ratios, scales_per_octave,
          normalize_coordinates)
    else:
      first_stage_anchor_scales = (0.001, 0.005, 0.1)
      first_stage_anchor_aspect_ratios = (0.5, 1.0, 2.0)
      first_stage_anchor_strides = (1, 1)
      first_stage_anchor_generator = grid_anchor_generator.GridAnchorGenerator(
          first_stage_anchor_scales,
          first_stage_anchor_aspect_ratios,
          anchor_stride=first_stage_anchor_strides)
    first_stage_target_assigner = target_assigner.create_target_assigner(
        'FasterRCNN',
        'proposal',
        use_matmul_gather=use_matmul_gather_in_matcher)

    if use_keras:
      if multi_level:
        fake_feature_extractor = FakeFasterRCNNKerasMultilevelFeatureExtractor()
      else:
        fake_feature_extractor = FakeFasterRCNNKerasFeatureExtractor()
    else:
      if multi_level:
        fake_feature_extractor = FakeFasterRCNNMultiLevelFeatureExtractor()
      else:
        fake_feature_extractor = FakeFasterRCNNFeatureExtractor()

    first_stage_box_predictor_hyperparams_text_proto = """
      op: CONV
      activation: RELU
      regularizer {
        l2_regularizer {
          weight: 0.00004
        }
      }
      initializer {
        truncated_normal_initializer {
          stddev: 0.03
        }
      }
    """
    if use_keras:
      first_stage_box_predictor_arg_scope_fn = (
          self._build_keras_layer_hyperparams(
              first_stage_box_predictor_hyperparams_text_proto))
    else:
      first_stage_box_predictor_arg_scope_fn = (
          self._build_arg_scope_with_hyperparams(
              first_stage_box_predictor_hyperparams_text_proto, is_training))

    first_stage_box_predictor_kernel_size = 3
    first_stage_atrous_rate = 1
    first_stage_box_predictor_depth = 512
    first_stage_minibatch_size = 3
    first_stage_sampler = sampler.BalancedPositiveNegativeSampler(
        positive_fraction=0.5, is_static=use_static_shapes)

    first_stage_nms_score_threshold = -1.0
    first_stage_nms_iou_threshold = 1.0
    first_stage_max_proposals = first_stage_max_proposals
    first_stage_non_max_suppression_fn = functools.partial(
        post_processing.batch_multiclass_non_max_suppression,
        score_thresh=first_stage_nms_score_threshold,
        iou_thresh=first_stage_nms_iou_threshold,
        max_size_per_class=first_stage_max_proposals,
        max_total_size=first_stage_max_proposals,
        use_static_shapes=use_static_shapes)

    first_stage_localization_loss_weight = 1.0
    first_stage_objectness_loss_weight = 1.0

    post_processing_config = post_processing_pb2.PostProcessing()
    post_processing_text_proto = """
      score_converter: IDENTITY
      batch_non_max_suppression {
        score_threshold: -20.0
        iou_threshold: 1.0
        max_detections_per_class: 5
        max_total_detections: 5
        use_static_shapes: """ +'{}'.format(use_static_shapes) + """
      }
    """
    if calibration_mapping_value:
      calibration_text_proto = """
      calibration_config {
        function_approximation {
          x_y_pairs {
            x_y_pair {
              x: 0.0
              y: %f
            }
            x_y_pair {
              x: 1.0
              y: %f
              }}}}""" % (calibration_mapping_value, calibration_mapping_value)
      post_processing_text_proto = (post_processing_text_proto
                                    + ' ' + calibration_text_proto)
    text_format.Merge(post_processing_text_proto, post_processing_config)
    second_stage_non_max_suppression_fn, second_stage_score_conversion_fn = (
        post_processing_builder.build(post_processing_config))

    second_stage_target_assigner = target_assigner.create_target_assigner(
        'FasterRCNN', 'detection',
        use_matmul_gather=use_matmul_gather_in_matcher)
    second_stage_sampler = sampler.BalancedPositiveNegativeSampler(
        positive_fraction=1.0, is_static=use_static_shapes)

    second_stage_localization_loss_weight = 1.0
    second_stage_classification_loss_weight = 1.0
    if softmax_second_stage_classification_loss:
      second_stage_classification_loss = (
          losses.WeightedSoftmaxClassificationLoss())
    else:
      second_stage_classification_loss = (
          losses.WeightedSigmoidClassificationLoss())

    hard_example_miner = None
    if hard_mining:
      hard_example_miner = losses.HardExampleMiner(
          num_hard_examples=1,
          iou_threshold=0.99,
          loss_type='both',
          cls_loss_weight=second_stage_classification_loss_weight,
          loc_loss_weight=second_stage_localization_loss_weight,
          max_negatives_per_positive=None)

    crop_and_resize_fn = (
        spatial_ops.multilevel_matmul_crop_and_resize
        if use_matmul_crop_and_resize
        else spatial_ops.multilevel_native_crop_and_resize)
    common_kwargs = {
        'is_training':
            is_training,
        'num_classes':
            num_classes,
        'image_resizer_fn':
            image_resizer_fn,
        'feature_extractor':
            fake_feature_extractor,
        'number_of_stages':
            number_of_stages,
        'first_stage_anchor_generator':
            first_stage_anchor_generator,
        'first_stage_target_assigner':
            first_stage_target_assigner,
        'first_stage_atrous_rate':
            first_stage_atrous_rate,
        'first_stage_box_predictor_arg_scope_fn':
            first_stage_box_predictor_arg_scope_fn,
        'first_stage_box_predictor_kernel_size':
            first_stage_box_predictor_kernel_size,
        'first_stage_box_predictor_depth':
            first_stage_box_predictor_depth,
        'first_stage_minibatch_size':
            first_stage_minibatch_size,
        'first_stage_sampler':
            first_stage_sampler,
        'first_stage_non_max_suppression_fn':
            first_stage_non_max_suppression_fn,
        'first_stage_max_proposals':
            first_stage_max_proposals,
        'first_stage_localization_loss_weight':
            first_stage_localization_loss_weight,
        'first_stage_objectness_loss_weight':
            first_stage_objectness_loss_weight,
        'second_stage_target_assigner':
            second_stage_target_assigner,
        'second_stage_batch_size':
            second_stage_batch_size,
        'second_stage_sampler':
            second_stage_sampler,
        'second_stage_non_max_suppression_fn':
            second_stage_non_max_suppression_fn,
        'second_stage_score_conversion_fn':
            second_stage_score_conversion_fn,
        'second_stage_localization_loss_weight':
            second_stage_localization_loss_weight,
        'second_stage_classification_loss_weight':
            second_stage_classification_loss_weight,
        'second_stage_classification_loss':
            second_stage_classification_loss,
        'hard_example_miner':
            hard_example_miner,
        'crop_and_resize_fn':
            crop_and_resize_fn,
        'clip_anchors_to_image':
            clip_anchors_to_image,
        'use_static_shapes':
            use_static_shapes,
        'resize_masks':
            True,
        'return_raw_detections_during_predict':
            return_raw_detections_during_predict,
        'output_final_box_features':
            output_final_box_features
    }

    return self._get_model(
        self._get_second_stage_box_predictor(
            num_classes=num_classes,
            is_training=is_training,
            use_keras=use_keras,
            predict_masks=predict_masks,
            masks_are_class_agnostic=masks_are_class_agnostic,
            share_box_across_classes=share_box_across_classes), **common_kwargs)