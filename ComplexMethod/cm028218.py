def build(self, input_shape):
    full_mobilenet_v2 = mobilenet_v2.mobilenet_v2(
        batchnorm_training=(self._is_training and not self._freeze_batchnorm),
        conv_hyperparams=(self._conv_hyperparams
                          if self._override_base_feature_extractor_hyperparams
                          else None),
        weights=None,
        use_explicit_padding=self._use_explicit_padding,
        alpha=self._depth_multiplier,
        min_depth=self._min_depth,
        include_top=False,
        input_shape=(None, None, input_shape[-1]))
    layer_names = [layer.name for layer in full_mobilenet_v2.layers]
    outputs = []
    for layer_idx in [4, 7, 14]:
      add_name = 'block_{}_add'.format(layer_idx - 2)
      project_name = 'block_{}_project_BN'.format(layer_idx - 2)
      output_layer_name = add_name if add_name in layer_names else project_name
      outputs.append(full_mobilenet_v2.get_layer(output_layer_name).output)
    layer_19 = full_mobilenet_v2.get_layer(name='out_relu').output
    outputs.append(layer_19)
    self.classification_backbone = tf.keras.Model(
        inputs=full_mobilenet_v2.inputs,
        outputs=outputs)
    # pylint:disable=g-long-lambda
    self._depth_fn = lambda d: max(
        int(d * self._depth_multiplier), self._min_depth)
    self._base_fpn_max_level = min(self._fpn_max_level, 5)
    self._num_levels = self._base_fpn_max_level + 1 - self._fpn_min_level
    self._fpn_features_generator = (
        feature_map_generators.KerasFpnTopDownFeatureMaps(
            num_levels=self._num_levels,
            depth=self._depth_fn(self._additional_layer_depth),
            use_depthwise=self._use_depthwise,
            use_explicit_padding=self._use_explicit_padding,
            use_native_resize_op=self._use_native_resize_op,
            is_training=self._is_training,
            conv_hyperparams=self._conv_hyperparams,
            freeze_batchnorm=self._freeze_batchnorm,
            name='FeatureMaps'))
    # Construct coarse feature layers
    padding = 'VALID' if self._use_explicit_padding else 'SAME'
    kernel_size = 3
    stride = 2
    for i in range(self._base_fpn_max_level + 1, self._fpn_max_level + 1):
      coarse_feature_layers = []
      if self._use_explicit_padding:
        def fixed_padding(features, kernel_size=kernel_size):
          return ops.fixed_padding(features, kernel_size)
        coarse_feature_layers.append(tf.keras.layers.Lambda(
            fixed_padding, name='fixed_padding'))
      layer_name = 'bottom_up_Conv2d_{}'.format(
          i - self._base_fpn_max_level + NUM_LAYERS)
      conv_block = feature_map_generators.create_conv_block(
          self._use_depthwise, kernel_size, padding, stride, layer_name,
          self._conv_hyperparams, self._is_training, self._freeze_batchnorm,
          self._depth_fn(self._additional_layer_depth))
      coarse_feature_layers.extend(conv_block)
      self._coarse_feature_layers.append(coarse_feature_layers)
    self.built = True