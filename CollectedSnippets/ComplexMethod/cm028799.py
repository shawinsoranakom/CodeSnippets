def build_retinanet(
    input_specs: tf_keras.layers.InputSpec,
    model_config: retinanet_cfg.RetinaNet,
    l2_regularizer: Optional[tf_keras.regularizers.Regularizer] = None,
    backbone: Optional[tf_keras.Model] = None,
    decoder: Optional[tf_keras.Model] = None,
    num_anchors_per_location: int | dict[str, int] | None = None,
    anchor_boxes: Mapping[str, tf.Tensor] | None = None,
) -> tf_keras.Model:
  """Builds a RetinaNet model.

  Args:
    input_specs: The InputSpec of the input image tensor to the model.
    model_config: The RetinaNet model configuration to build from.
    l2_regularizer: Optional l2 regularizer to use for building the backbone, 
      decorder, and head.
    backbone: Optional instance of the backbone model.
    decoder: Optional instance of the decoder model.
    num_anchors_per_location: Optional number of anchors per pixel location for
      building the RetinaNetHead. If an `int`, the same number is used for all
      levels. If a `dict`, it specifies the number at each level. If `none`, it
      uses `len(aspect_ratios) * num_scales` from the anchor config by default.
    anchor_boxes: Optional fixed multilevel anchor boxes for inference.

  Returns:
    RetinaNet model.
  """
  norm_activation_config = model_config.norm_activation
  if not backbone:
    backbone = backbones.factory.build_backbone(
        input_specs=input_specs,
        backbone_config=model_config.backbone,
        norm_activation_config=norm_activation_config,
        l2_regularizer=l2_regularizer)
  backbone_features = backbone(tf_keras.Input(input_specs.shape[1:]))

  if not decoder:
    decoder = decoders.factory.build_decoder(
        input_specs=backbone.output_specs,
        model_config=model_config,
        l2_regularizer=l2_regularizer)

  head_config = model_config.head
  generator_config = model_config.detection_generator
  num_anchors_per_location = num_anchors_per_location or (
      len(model_config.anchor.aspect_ratios) * model_config.anchor.num_scales)

  head = dense_prediction_heads.RetinaNetHead(
      min_level=model_config.min_level,
      max_level=model_config.max_level,
      num_classes=model_config.num_classes,
      num_anchors_per_location=num_anchors_per_location,
      num_convs=head_config.num_convs,
      num_filters=head_config.num_filters,
      attribute_heads=[
          cfg.as_dict() for cfg in (head_config.attribute_heads or [])
      ],
      share_classification_heads=head_config.share_classification_heads,
      use_separable_conv=head_config.use_separable_conv,
      activation=norm_activation_config.activation,
      use_sync_bn=norm_activation_config.use_sync_bn,
      norm_momentum=norm_activation_config.norm_momentum,
      norm_epsilon=norm_activation_config.norm_epsilon,
      kernel_regularizer=l2_regularizer,
      share_level_convs=head_config.share_level_convs,
  )

  # Builds decoder and head so that their trainable weights are initialized
  if decoder:
    decoder_features = decoder(backbone_features)
    _ = head(decoder_features)

  # Add `input_image_size` into `tflite_post_processing_config`.
  tflite_post_processing_config = (
      generator_config.tflite_post_processing.as_dict()
  )
  tflite_post_processing_config['input_image_size'] = (
      input_specs.shape[1],
      input_specs.shape[2],
  )
  detection_generator_obj = detection_generator.MultilevelDetectionGenerator(
      apply_nms=generator_config.apply_nms,
      pre_nms_top_k=generator_config.pre_nms_top_k,
      pre_nms_score_threshold=generator_config.pre_nms_score_threshold,
      nms_iou_threshold=generator_config.nms_iou_threshold,
      max_num_detections=generator_config.max_num_detections,
      nms_version=generator_config.nms_version,
      use_cpu_nms=generator_config.use_cpu_nms,
      soft_nms_sigma=generator_config.soft_nms_sigma,
      tflite_post_processing_config=tflite_post_processing_config,
      return_decoded=generator_config.return_decoded,
      use_class_agnostic_nms=generator_config.use_class_agnostic_nms,
      box_coder_weights=generator_config.box_coder_weights,
  )

  num_scales = None
  aspect_ratios = None
  anchor_size = None
  if anchor_boxes is None:
    num_scales = model_config.anchor.num_scales
    aspect_ratios = model_config.anchor.aspect_ratios
    anchor_size = model_config.anchor.anchor_size

  model = retinanet_model.RetinaNetModel(
      backbone,
      decoder,
      head,
      detection_generator_obj,
      anchor_boxes=anchor_boxes,
      min_level=model_config.min_level,
      max_level=model_config.max_level,
      num_scales=num_scales,
      aspect_ratios=aspect_ratios,
      anchor_size=anchor_size,
  )
  return model