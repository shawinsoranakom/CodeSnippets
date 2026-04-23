def build_yolo_decoder(
    input_specs: Mapping[str, tf.TensorShape],
    model_config: hyperparams.Config,
    l2_regularizer: Optional[tf_keras.regularizers.Regularizer] = None,
    **kwargs) -> Union[None, tf_keras.Model, tf_keras.layers.Layer]:
  """Builds Yolo FPN/PAN decoder from a config.

  Args:
    input_specs: A `dict` of input specifications. A dictionary consists of
      {level: TensorShape} from a backbone.
    model_config: A OneOfConfig. Model config.
    l2_regularizer: A `tf_keras.regularizers.Regularizer` instance. Default to
      None.
    **kwargs: Additional kwargs arguments.

  Returns:
    A `tf_keras.Model` instance of the Yolo FPN/PAN decoder.
  """
  decoder_cfg = model_config.decoder.get()
  norm_activation_config = model_config.norm_activation

  activation = (
      decoder_cfg.activation if decoder_cfg.activation != 'same' else
      norm_activation_config.activation)

  if decoder_cfg.version is None:  # custom yolo
    raise ValueError('Decoder version cannot be None, specify v3 or v4.')

  if decoder_cfg.version not in YOLO_MODELS:
    raise ValueError(
        'Unsupported model version please select from {v3, v4}, '
        'or specify a custom decoder config using YoloDecoder in you yaml')

  if decoder_cfg.type is None:
    decoder_cfg.type = 'regular'

  if decoder_cfg.type not in YOLO_MODELS[decoder_cfg.version]:
    raise ValueError('Unsupported model type please select from '
                     '{yolo_model.YOLO_MODELS[decoder_cfg.version].keys()}'
                     'or specify a custom decoder config using YoloDecoder.')

  base_model = YOLO_MODELS[decoder_cfg.version][decoder_cfg.type].copy()

  cfg_dict = decoder_cfg.as_dict()
  for key in base_model:
    if cfg_dict[key] is not None:
      base_model[key] = cfg_dict[key]

  base_dict = dict(
      activation=activation,
      use_spatial_attention=decoder_cfg.use_spatial_attention,
      use_separable_conv=decoder_cfg.use_separable_conv,
      use_sync_bn=norm_activation_config.use_sync_bn,
      norm_momentum=norm_activation_config.norm_momentum,
      norm_epsilon=norm_activation_config.norm_epsilon,
      kernel_regularizer=l2_regularizer)

  base_model.update(base_dict)
  model = YoloDecoder(input_specs, **base_model, **kwargs)
  return model