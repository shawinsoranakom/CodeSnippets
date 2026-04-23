def build(
      self,
      input_shape: Tuple[tf.TensorShape, tf.TensorShape]) -> None:
    """Builds the block with the given input shape."""
    # Assume backbone features of the same level are concated before input.
    low_res_input_shape = input_shape[0]
    high_res_input_shape = input_shape[1]
    low_res_channels = low_res_input_shape[self._channel_axis]
    high_res_channels = high_res_input_shape[self._channel_axis]

    # Override the activation and bn with their quantized version.
    self._activation_fn = tfmot.quantization.keras.QuantizeWrapperV2(
        tf_utils.get_activation(self._activation, use_keras_layer=True),
        configs.Default8BitActivationQuantizeConfig())
    norm_layer = (
        tf_keras.layers.experimental.SyncBatchNormalization
        if self._use_sync_bn else tf_keras.layers.BatchNormalization)
    norm_with_quantize = helper.BatchNormalizationQuantized(norm_layer)
    norm_no_quantize = helper.BatchNormalizationNoQuantized(norm_layer)
    self._bn_op = helper.norm_by_activation(
        self._activation, norm_with_quantize, norm_no_quantize)

    if low_res_channels != self._decoder_projected_depth:
      low_res_feature_conv = helper.Conv2DQuantized(
          filters=self._decoder_projected_depth,
          kernel_size=(1, 1),
          padding='same',
          kernel_regularizer=self._kernel_regularizer,
          kernel_initializer=self._kernel_initializer,
          activation=helper.NoOpActivation(),
          use_bias=False)
      batchnorm_op = self._bn_op(
          axis=self._bn_axis,
          momentum=self._batchnorm_momentum,
          epsilon=self._batchnorm_epsilon)
      self._low_res_branch = [
          low_res_feature_conv,
          batchnorm_op,
      ]
    if high_res_channels != self._decoder_projected_depth:
      high_res_feature_conv = helper.Conv2DQuantized(
          filters=self._decoder_projected_depth,
          kernel_size=(1, 1),
          padding='same',
          kernel_regularizer=self._kernel_regularizer,
          kernel_initializer=self._kernel_initializer,
          activation=helper.NoOpActivation(),
          use_bias=False)
      batchnorm_op_high = self._bn_op(
          axis=self._bn_axis,
          momentum=self._batchnorm_momentum,
          epsilon=self._batchnorm_epsilon)
      self._high_res_branch = [
          high_res_feature_conv,
          batchnorm_op_high,
      ]
    # Resize feature maps.
    if tf_keras.backend.image_data_format() == 'channels_last':
      low_res_height = low_res_input_shape[1]
      low_res_width = low_res_input_shape[2]
      high_res_height = high_res_input_shape[1]
      high_res_width = high_res_input_shape[2]
    else:
      low_res_height = low_res_input_shape[2]
      low_res_width = low_res_input_shape[3]
      high_res_height = high_res_input_shape[2]
      high_res_width = high_res_input_shape[3]
    if (self._output_size[0] == 0 or self._output_size[1] == 0):
      self._output_size = (high_res_height, high_res_width)
    if (low_res_height != self._output_size[0] or
        low_res_width != self._output_size[1]):
      self._upsample_low_res = helper.ResizingQuantized(
          self._output_size[0],
          self._output_size[1],
          interpolation=self._interpolation,
          crop_to_aspect_ratio=False)
    if (high_res_height != self._output_size[0] or
        high_res_width != self._output_size[1]):
      self._upsample_high_res = helper.ResizingQuantized(
          self._output_size[0],
          self._output_size[1],
          interpolation=self._interpolation,
          crop_to_aspect_ratio=False)
    self._add_layer = tfmot.quantization.keras.QuantizeWrapperV2(
        tf_keras.layers.Add(), configs.Default8BitQuantizeConfig([], [], True))