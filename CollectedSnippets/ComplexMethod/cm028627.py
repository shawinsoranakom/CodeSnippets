def __init__(self,
               model_config_name: Optional[str] = None,
               overrides: Optional[Mapping[str, Any]] = None,
               **kwargs):
    """Creates a MobilenetEdgeTPUV2 model.

    Args:
      model_config_name: (optional) the model parameters to create the model.
      overrides: (optional) a dict containing keys that can override config.
      **kwargs: All the rest model arguments in a dictionary.
    """
    self.model_config_name = model_config_name
    self._self_setattr_tracking = False
    self.overrides = overrides or {}

    if model_config_name is None:
      model_config = ModelConfig()
    else:
      if model_config_name not in MODEL_CONFIGS:
        supported_model_list = list(MODEL_CONFIGS.keys())
        raise ValueError(f'Unknown model name {model_config_name}. Only support'
                         f'model configs in {supported_model_list}.')
      model_config = MODEL_CONFIGS[model_config_name]

    self.config = model_config.replace(**self.overrides)

    input_channels = self.config.input_channels
    model_name = self.config.model_name
    if isinstance(self.config.resolution, tuple):
      input_shape = (self.config.resolution[0], self.config.resolution[1],
                     input_channels)
    else:
      input_shape = (self.config.resolution, self.config.resolution,
                     input_channels)
    image_input = tf_keras.layers.Input(shape=input_shape)

    output = mobilenet_edgetpu_v2_model_blocks.mobilenet_edgetpu_v2(
        image_input, self.config)

    if not isinstance(output, list):
      # Cast to float32 in case we have a different model dtype
      output = tf.cast(output, tf.float32)
      self._output_specs = output.get_shape()
    else:
      if self.config.features_as_dict:
        # Dict output is required for the decoder ASPP module.
        self._output_specs = {
            str(i): output[i].get_shape() for i in range(len(output))
        }
        output = {str(i): output[i] for i in range(len(output))}
      else:
        # edgetpu/tasks/segmentation assumes features as list.
        self._output_specs = [feat.get_shape() for feat in output]

    logging.info('Building model %s with params %s',
                 model_name,
                 self.config)

    super(MobilenetEdgeTPUV2, self).__init__(
        inputs=image_input, outputs=output, **kwargs)
    self._self_setattr_tracking = True