def build_keras(hyperparams_fn, freeze_batchnorm, inplace_batchnorm_update,
                num_predictions_per_location_list, box_predictor_config,
                is_training, num_classes, add_background_class=True):
  """Builds a Keras-based box predictor based on the configuration.

  Builds Keras-based box predictor based on the configuration.
  See box_predictor.proto for configurable options. Also, see box_predictor.py
  for more details.

  Args:
    hyperparams_fn: A function that takes a hyperparams_pb2.Hyperparams
      proto and returns a `hyperparams_builder.KerasLayerHyperparams`
      for Conv or FC hyperparameters.
    freeze_batchnorm: Whether to freeze batch norm parameters during
      training or not. When training with a small batch size (e.g. 1), it is
      desirable to freeze batch norm update and use pretrained batch norm
      params.
    inplace_batchnorm_update: Whether to update batch norm moving average
      values inplace. When this is false train op must add a control
      dependency on tf.graphkeys.UPDATE_OPS collection in order to update
      batch norm statistics.
    num_predictions_per_location_list: A list of integers representing the
      number of box predictions to be made per spatial location for each
      feature map.
    box_predictor_config: box_predictor_pb2.BoxPredictor proto containing
      configuration.
    is_training: Whether the models is in training mode.
    num_classes: Number of classes to predict.
    add_background_class: Whether to add an implicit background class.

  Returns:
    box_predictor: box_predictor.KerasBoxPredictor object.

  Raises:
    ValueError: On unknown box predictor, or one with no Keras box predictor.
  """
  if not isinstance(box_predictor_config, box_predictor_pb2.BoxPredictor):
    raise ValueError('box_predictor_config not of type '
                     'box_predictor_pb2.BoxPredictor.')

  box_predictor_oneof = box_predictor_config.WhichOneof('box_predictor_oneof')

  if box_predictor_oneof == 'convolutional_box_predictor':
    config_box_predictor = box_predictor_config.convolutional_box_predictor
    conv_hyperparams = hyperparams_fn(
        config_box_predictor.conv_hyperparams)
    # Optionally apply clipping to box encodings, when box_encodings_clip_range
    # is set.
    box_encodings_clip_range = None
    if config_box_predictor.HasField('box_encodings_clip_range'):
      box_encodings_clip_range = BoxEncodingsClipRange(
          min=config_box_predictor.box_encodings_clip_range.min,
          max=config_box_predictor.box_encodings_clip_range.max)

    return build_convolutional_keras_box_predictor(
        is_training=is_training,
        num_classes=num_classes,
        add_background_class=add_background_class,
        conv_hyperparams=conv_hyperparams,
        freeze_batchnorm=freeze_batchnorm,
        inplace_batchnorm_update=inplace_batchnorm_update,
        num_predictions_per_location_list=num_predictions_per_location_list,
        use_dropout=config_box_predictor.use_dropout,
        dropout_keep_prob=config_box_predictor.dropout_keep_probability,
        box_code_size=config_box_predictor.box_code_size,
        kernel_size=config_box_predictor.kernel_size,
        num_layers_before_predictor=(
            config_box_predictor.num_layers_before_predictor),
        min_depth=config_box_predictor.min_depth,
        max_depth=config_box_predictor.max_depth,
        class_prediction_bias_init=(
            config_box_predictor.class_prediction_bias_init),
        use_depthwise=config_box_predictor.use_depthwise,
        box_encodings_clip_range=box_encodings_clip_range)

  if box_predictor_oneof == 'weight_shared_convolutional_box_predictor':
    config_box_predictor = (
        box_predictor_config.weight_shared_convolutional_box_predictor)
    conv_hyperparams = hyperparams_fn(config_box_predictor.conv_hyperparams)
    apply_batch_norm = config_box_predictor.conv_hyperparams.HasField(
        'batch_norm')
    # During training phase, logits are used to compute the loss. Only apply
    # sigmoid at inference to make the inference graph TPU friendly. This is
    # required because during TPU inference, model.postprocess is not called.
    score_converter_fn = build_score_converter(
        config_box_predictor.score_converter, is_training)
    # Optionally apply clipping to box encodings, when box_encodings_clip_range
    # is set.
    box_encodings_clip_range = None
    if config_box_predictor.HasField('box_encodings_clip_range'):
      box_encodings_clip_range = BoxEncodingsClipRange(
          min=config_box_predictor.box_encodings_clip_range.min,
          max=config_box_predictor.box_encodings_clip_range.max)
    keyword_args = None

    return build_weight_shared_convolutional_keras_box_predictor(
        is_training=is_training,
        num_classes=num_classes,
        conv_hyperparams=conv_hyperparams,
        freeze_batchnorm=freeze_batchnorm,
        inplace_batchnorm_update=inplace_batchnorm_update,
        num_predictions_per_location_list=num_predictions_per_location_list,
        depth=config_box_predictor.depth,
        num_layers_before_predictor=(
            config_box_predictor.num_layers_before_predictor),
        box_code_size=config_box_predictor.box_code_size,
        kernel_size=config_box_predictor.kernel_size,
        add_background_class=add_background_class,
        class_prediction_bias_init=(
            config_box_predictor.class_prediction_bias_init),
        use_dropout=config_box_predictor.use_dropout,
        dropout_keep_prob=config_box_predictor.dropout_keep_probability,
        share_prediction_tower=config_box_predictor.share_prediction_tower,
        apply_batch_norm=apply_batch_norm,
        use_depthwise=config_box_predictor.use_depthwise,
        apply_conv_hyperparams_to_heads=(
            config_box_predictor.apply_conv_hyperparams_to_heads),
        apply_conv_hyperparams_pointwise=(
            config_box_predictor.apply_conv_hyperparams_pointwise),
        score_converter_fn=score_converter_fn,
        box_encodings_clip_range=box_encodings_clip_range,
        keyword_args=keyword_args)

  if box_predictor_oneof == 'mask_rcnn_box_predictor':
    config_box_predictor = box_predictor_config.mask_rcnn_box_predictor
    fc_hyperparams = hyperparams_fn(config_box_predictor.fc_hyperparams)
    conv_hyperparams = None
    if config_box_predictor.HasField('conv_hyperparams'):
      conv_hyperparams = hyperparams_fn(
          config_box_predictor.conv_hyperparams)
    return build_mask_rcnn_keras_box_predictor(
        is_training=is_training,
        num_classes=num_classes,
        add_background_class=add_background_class,
        fc_hyperparams=fc_hyperparams,
        freeze_batchnorm=freeze_batchnorm,
        use_dropout=config_box_predictor.use_dropout,
        dropout_keep_prob=config_box_predictor.dropout_keep_probability,
        box_code_size=config_box_predictor.box_code_size,
        share_box_across_classes=(
            config_box_predictor.share_box_across_classes),
        predict_instance_masks=config_box_predictor.predict_instance_masks,
        conv_hyperparams=conv_hyperparams,
        mask_height=config_box_predictor.mask_height,
        mask_width=config_box_predictor.mask_width,
        mask_prediction_num_conv_layers=(
            config_box_predictor.mask_prediction_num_conv_layers),
        mask_prediction_conv_depth=(
            config_box_predictor.mask_prediction_conv_depth),
        masks_are_class_agnostic=(
            config_box_predictor.masks_are_class_agnostic),
        convolve_then_upsample_masks=(
            config_box_predictor.convolve_then_upsample_masks))

  if box_predictor_oneof == 'rfcn_box_predictor':
    config_box_predictor = box_predictor_config.rfcn_box_predictor
    conv_hyperparams = hyperparams_fn(config_box_predictor.conv_hyperparams)
    box_predictor_object = rfcn_keras_box_predictor.RfcnKerasBoxPredictor(
        is_training=is_training,
        num_classes=num_classes,
        conv_hyperparams=conv_hyperparams,
        freeze_batchnorm=freeze_batchnorm,
        crop_size=[config_box_predictor.crop_height,
                   config_box_predictor.crop_width],
        num_spatial_bins=[config_box_predictor.num_spatial_bins_height,
                          config_box_predictor.num_spatial_bins_width],
        depth=config_box_predictor.depth,
        box_code_size=config_box_predictor.box_code_size)
    return box_predictor_object

  raise ValueError(
      'Unknown box predictor for Keras: {}'.format(box_predictor_oneof))