def build(self, input_shape: Union[tf.TensorShape, List[tf.TensorShape]]):
    """Creates the variables of the segmentation head."""
    use_depthwise_convolution = self._config_dict['use_depthwise_convolution']
    conv_op = tf_keras.layers.Conv2D
    if self._config_dict['use_layer_norm']:
      bn_layer = lambda: tf_keras.layers.LayerNormalization(epsilon=1e-6)
    else:
      bn_kwargs = {
          'axis': self._bn_axis,
          'momentum': self._config_dict['norm_momentum'],
          'epsilon': self._config_dict['norm_epsilon'],
      }
      if self._config_dict['use_sync_bn']:
        bn_layer = lambda: tf_keras.layers.experimental.SyncBatchNormalization(  # pylint: disable=g-long-lambda
            **bn_kwargs)
      else:
        bn_layer = lambda: tf_keras.layers.BatchNormalization(**bn_kwargs)

    if self._config_dict['feature_fusion'] in {'deeplabv3plus',
                                               'deeplabv3plus_sum_to_merge'}:
      # Deeplabv3+ feature fusion layers.
      self._dlv3p_conv = conv_op(
          kernel_size=1,
          padding='same',
          use_bias=False,
          kernel_initializer=tf_keras.initializers.he_normal(),
          kernel_regularizer=self._config_dict['kernel_regularizer'],
          name='segmentation_head_deeplabv3p_fusion_conv',
          filters=self._config_dict['low_level_num_filters'])

      self._dlv3p_norm = bn_layer()

    elif self._config_dict['feature_fusion'] == 'panoptic_fpn_fusion':
      self._panoptic_fpn_fusion = nn_layers.PanopticFPNFusion(
          min_level=self._config_dict['decoder_min_level'],
          max_level=self._config_dict['decoder_max_level'],
          target_level=self._config_dict['level'],
          num_filters=self._config_dict['num_filters'],
          num_fpn_filters=self._config_dict['num_decoder_filters'],
          activation=self._config_dict['activation'],
          kernel_regularizer=self._config_dict['kernel_regularizer'],
          bias_regularizer=self._config_dict['bias_regularizer'])

    # Segmentation head layers.
    self._convs = []
    self._norms = []
    for i in range(self._config_dict['num_convs']):
      if use_depthwise_convolution:
        self._convs.append(
            tf_keras.layers.DepthwiseConv2D(
                name='segmentation_head_depthwise_conv_{}'.format(i),
                kernel_size=self._config_dict['depthwise_kernel_size'],
                padding='same',
                use_bias=False,
                depth_multiplier=1))
        self._norms.append(bn_layer())
      conv_name = 'segmentation_head_conv_{}'.format(i)
      self._convs.append(
          conv_op(
              name=conv_name,
              filters=self._config_dict['num_filters'],
              kernel_size=3 if not use_depthwise_convolution else 1,
              padding='same',
              use_bias=False,
              kernel_initializer=tf_keras.initializers.he_normal(),
              kernel_regularizer=self._config_dict['kernel_regularizer']))
      self._norms.append(bn_layer())

    self._classifier = conv_op(
        name='segmentation_output',
        filters=self._config_dict['num_classes'],
        kernel_size=self._config_dict['prediction_kernel_size'],
        padding='same',
        bias_initializer=self._config_dict['bias_initializer'],
        kernel_initializer=tf_keras.initializers.truncated_normal(stddev=0.01),
        kernel_regularizer=self._config_dict['kernel_regularizer'],
        bias_regularizer=self._config_dict['bias_regularizer'])

    super().build(input_shape)