def build(
      self,
      input_shape: Tuple[tf.TensorShape, tf.TensorShape]) -> None:
    """Builds this block with the given input shape."""
    # Assume backbone features of the same level are concated before input.
    low_res_input_shape = input_shape[0]
    high_res_input_shape = input_shape[1]
    # Set up resizing feature maps before concat.
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
      self._upsample_low_res = tf_keras.layers.Resizing(
          self._output_size[0],
          self._output_size[1],
          interpolation=self._interpolation,
          crop_to_aspect_ratio=False)
    if (high_res_height != self._output_size[0] or
        high_res_width != self._output_size[1]):
      self._upsample_high_res = tf_keras.layers.Resizing(
          self._output_size[0],
          self._output_size[1],
          interpolation=self._interpolation,
          crop_to_aspect_ratio=False)
    # Set up a 3-layer separable convolution blocks, i.e.
    # 1x1->BN->RELU + Depthwise->BN->RELU + 1x1->BN->RELU.
    initial_feature_conv = tf_keras.layers.Conv2D(
        filters=self._decoder_internal_depth,
        kernel_size=(1, 1),
        padding='same',
        kernel_regularizer=self._kernel_regularizer,
        kernel_initializer=self._kernel_initializer,
        activation=None,
        use_bias=False)
    batchnorm_op1 = self._bn_op(
        axis=self._bn_axis,
        momentum=self._batchnorm_momentum,
        epsilon=self._batchnorm_epsilon)
    activation1 = self._activation_fn
    depthwise_conv = tf_keras.layers.DepthwiseConv2D(
        kernel_size=(3, 3),
        depth_multiplier=1,
        padding='same',
        depthwise_regularizer=self._kernel_regularizer,
        depthwise_initializer=self._kernel_initializer,
        use_bias=False)
    batchnorm_op2 = self._bn_op(
        axis=self._bn_axis,
        momentum=self._batchnorm_momentum,
        epsilon=self._batchnorm_epsilon)
    activation2 = self._activation_fn
    project_feature_conv = tf_keras.layers.Conv2D(
        filters=self._decoder_projected_depth,
        kernel_size=(1, 1),
        padding='same',
        kernel_regularizer=self._kernel_regularizer,
        kernel_initializer=self._kernel_initializer,
        activation=None,
        use_bias=False)
    batchnorm_op3 = self._bn_op(
        axis=self._bn_axis,
        momentum=self._batchnorm_momentum,
        epsilon=self._batchnorm_epsilon)
    activation3 = self._activation_fn
    self._feature_fusion_block = [
        initial_feature_conv,
        batchnorm_op1,
        activation1,
        depthwise_conv,
        batchnorm_op2,
        activation2,
        project_feature_conv,
        batchnorm_op3,
        activation3,
        ]
    self._concat_layer = tf_keras.layers.Concatenate(axis=self._channel_axis)