def _compute_base_tower(self, tower_name_scope, feature_index):
    conv_layers = []
    batch_norm_layers = []
    activation_layers = []
    use_bias = False if (self._apply_batch_norm and not
                         self._conv_hyperparams.force_use_bias()) else True
    for additional_conv_layer_idx in range(self._num_layers_before_predictor):
      layer_name = '{}/conv2d_{}'.format(
          tower_name_scope, additional_conv_layer_idx)
      if tower_name_scope not in self._head_scope_conv_layers:
        if self._use_depthwise:
          kwargs = self._conv_hyperparams.params(use_bias=use_bias)
          # Both the regularizer and initializer apply to the depthwise layer,
          # so we remap the kernel_* to depthwise_* here.
          kwargs['depthwise_regularizer'] = kwargs['kernel_regularizer']
          kwargs['depthwise_initializer'] = kwargs['kernel_initializer']
          if self._apply_conv_hyperparams_pointwise:
            kwargs['pointwise_regularizer'] = kwargs['kernel_regularizer']
            kwargs['pointwise_initializer'] = kwargs['kernel_initializer']
          conv_layers.append(
              tf.keras.layers.SeparableConv2D(
                  self._depth, [self._kernel_size, self._kernel_size],
                  padding='SAME',
                  name=layer_name,
                  **kwargs))
        else:
          conv_layers.append(
              tf.keras.layers.Conv2D(
                  self._depth,
                  [self._kernel_size, self._kernel_size],
                  padding='SAME',
                  name=layer_name,
                  **self._conv_hyperparams.params(use_bias=use_bias)))
      # Each feature gets a separate batchnorm parameter even though they share
      # the same convolution weights.
      if self._apply_batch_norm:
        batch_norm_layers.append(self._conv_hyperparams.build_batch_norm(
            training=(self._is_training and not self._freeze_batchnorm),
            name='{}/conv2d_{}/BatchNorm/feature_{}'.format(
                tower_name_scope, additional_conv_layer_idx, feature_index)))
      activation_layers.append(self._conv_hyperparams.build_activation_layer(
          name='{}/conv2d_{}/activation_{}'.format(
              tower_name_scope, additional_conv_layer_idx, feature_index)))

    # Set conv layers as the shared conv layers for different feature maps with
    # the same tower_name_scope.
    if tower_name_scope in self._head_scope_conv_layers:
      conv_layers = self._head_scope_conv_layers[tower_name_scope]

    # Stack the base_tower_layers in the order of conv_layer, batch_norm_layer
    # and activation_layer
    base_tower_layers = []
    for i in range(self._num_layers_before_predictor):
      base_tower_layers.extend([conv_layers[i]])
      if self._apply_batch_norm:
        base_tower_layers.extend([batch_norm_layers[i]])
      base_tower_layers.extend([activation_layers[i]])
    return conv_layers, base_tower_layers