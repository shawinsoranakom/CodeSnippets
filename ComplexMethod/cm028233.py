def Conv2D(self, filters, **kwargs):
    """Builds a Conv2D layer according to the current Object Detection config.

    Overrides the Keras MobileNetV2 application's convolutions with ones that
    follow the spec specified by the Object Detection hyperparameters.

    Args:
      filters: The number of filters to use for the convolution.
      **kwargs: Keyword args specified by the Keras application for
        constructing the convolution.

    Returns:
      A one-arg callable that will either directly apply a Keras Conv2D layer to
      the input argument, or that will first pad the input then apply a Conv2D
      layer.
    """
    # Make sure 'alpha' is always applied to the last convolution block's size
    # (This overrides the Keras application's functionality)
    layer_name = kwargs.get('name')
    if layer_name == 'Conv_1':
      if self._conv_defs:
        filters = model_utils.get_conv_def(self._conv_defs, 'Conv_1')
      else:
        filters = 1280
      if self._alpha < 1.0:
        filters = _make_divisible(filters * self._alpha, 8)

    # Apply the minimum depth to the convolution layers
    if (self._min_depth and (filters < self._min_depth)
        and not kwargs.get('name').endswith('expand')):
      filters = self._min_depth

    if self._conv_hyperparams:
      kwargs = self._conv_hyperparams.params(**kwargs)
    else:
      kwargs['kernel_regularizer'] = self.regularizer
      kwargs['kernel_initializer'] = self.initializer

    kwargs['padding'] = 'same'
    kernel_size = kwargs.get('kernel_size')
    if self._use_explicit_padding and kernel_size > 1:
      kwargs['padding'] = 'valid'
      def padded_conv(features):
        padded_features = self._FixedPaddingLayer(kernel_size)(features)
        return tf.keras.layers.Conv2D(filters, **kwargs)(padded_features)

      return padded_conv
    else:
      return tf.keras.layers.Conv2D(filters, **kwargs)