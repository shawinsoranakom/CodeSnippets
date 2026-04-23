def _create_model(
      self,
      model_fn=ssd_meta_arch.SSDMetaArch,
      apply_hard_mining=True,
      normalize_loc_loss_by_codesize=False,
      add_background_class=True,
      random_example_sampling=False,
      expected_loss_weights=model_pb2.DetectionModel().ssd.loss.NONE,
      min_num_negative_samples=1,
      desired_negative_sampling_ratio=3,
      predict_mask=False,
      use_static_shapes=False,
      nms_max_size_per_class=5,
      calibration_mapping_value=None,
      return_raw_detections_during_predict=False):
    is_training = False
    num_classes = 1
    mock_anchor_generator = MockAnchorGenerator2x2()
    use_keras = tf_version.is_tf2()
    if use_keras:
      mock_box_predictor = test_utils.MockKerasBoxPredictor(
          is_training, num_classes, add_background_class=add_background_class)
    else:
      mock_box_predictor = test_utils.MockBoxPredictor(
          is_training, num_classes, add_background_class=add_background_class)
    mock_box_coder = test_utils.MockBoxCoder()
    if use_keras:
      fake_feature_extractor = FakeSSDKerasFeatureExtractor()
    else:
      fake_feature_extractor = FakeSSDFeatureExtractor()
    mock_matcher = test_utils.MockMatcher()
    region_similarity_calculator = sim_calc.IouSimilarity()
    encode_background_as_zeros = False

    def image_resizer_fn(image):
      return [tf.identity(image), tf.shape(image)]

    classification_loss = losses.WeightedSigmoidClassificationLoss()
    localization_loss = losses.WeightedSmoothL1LocalizationLoss()
    non_max_suppression_fn = functools.partial(
        post_processing.batch_multiclass_non_max_suppression,
        score_thresh=-20.0,
        iou_thresh=1.0,
        max_size_per_class=nms_max_size_per_class,
        max_total_size=nms_max_size_per_class,
        use_static_shapes=use_static_shapes)
    score_conversion_fn = tf.identity
    calibration_config = calibration_pb2.CalibrationConfig()
    if calibration_mapping_value:
      calibration_text_proto = """
      function_approximation {
        x_y_pairs {
            x_y_pair {
              x: 0.0
              y: %f
            }
            x_y_pair {
              x: 1.0
              y: %f
            }}}""" % (calibration_mapping_value, calibration_mapping_value)
      text_format.Merge(calibration_text_proto, calibration_config)
      score_conversion_fn = (
          post_processing_builder._build_calibrated_score_converter(  # pylint: disable=protected-access
              tf.identity, calibration_config))
    classification_loss_weight = 1.0
    localization_loss_weight = 1.0
    negative_class_weight = 1.0
    normalize_loss_by_num_matches = False

    hard_example_miner = None
    if apply_hard_mining:
      # This hard example miner is expected to be a no-op.
      hard_example_miner = losses.HardExampleMiner(
          num_hard_examples=None, iou_threshold=1.0)

    random_example_sampler = None
    if random_example_sampling:
      random_example_sampler = sampler.BalancedPositiveNegativeSampler(
          positive_fraction=0.5)

    target_assigner_instance = target_assigner.TargetAssigner(
        region_similarity_calculator,
        mock_matcher,
        mock_box_coder,
        negative_class_weight=negative_class_weight)

    model_config = model_pb2.DetectionModel()
    if expected_loss_weights == model_config.ssd.loss.NONE:
      expected_loss_weights_fn = None
    else:
      raise ValueError('Not a valid value for expected_loss_weights.')

    code_size = 4

    kwargs = {}
    if predict_mask:
      kwargs.update({
          'mask_prediction_fn': test_utils.MockMaskHead(num_classes=1).predict,
      })

    model = model_fn(
        is_training=is_training,
        anchor_generator=mock_anchor_generator,
        box_predictor=mock_box_predictor,
        box_coder=mock_box_coder,
        feature_extractor=fake_feature_extractor,
        encode_background_as_zeros=encode_background_as_zeros,
        image_resizer_fn=image_resizer_fn,
        non_max_suppression_fn=non_max_suppression_fn,
        score_conversion_fn=score_conversion_fn,
        classification_loss=classification_loss,
        localization_loss=localization_loss,
        classification_loss_weight=classification_loss_weight,
        localization_loss_weight=localization_loss_weight,
        normalize_loss_by_num_matches=normalize_loss_by_num_matches,
        hard_example_miner=hard_example_miner,
        target_assigner_instance=target_assigner_instance,
        add_summaries=False,
        normalize_loc_loss_by_codesize=normalize_loc_loss_by_codesize,
        freeze_batchnorm=False,
        inplace_batchnorm_update=False,
        add_background_class=add_background_class,
        random_example_sampler=random_example_sampler,
        expected_loss_weights_fn=expected_loss_weights_fn,
        return_raw_detections_during_predict=(
            return_raw_detections_during_predict),
        **kwargs)
    return model, num_classes, mock_anchor_generator.num_anchors(), code_size