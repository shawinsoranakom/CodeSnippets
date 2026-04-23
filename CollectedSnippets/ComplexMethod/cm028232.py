def Conv2D(self, filters, kernel_size, **kwargs):
    """Builds a Conv2D layer according to the current Object Detection config.

    Overrides the Keras MobileNetV1 application's convolutions with ones that
    follow the spec specified by the Object Detection hyperparameters.

    Args:
      filters: The number of filters to use for the convolution.
      kernel_size: The kernel size to specify the height and width of the 2D
        convolution window. In this function, the kernel size is expected to
        be pair of numbers and the numbers must be equal for this function.
      **kwargs: Keyword args specified by the Keras application for
        constructing the convolution.

    Returns:
      A one-arg callable that will either directly apply a Keras Conv2D layer to
      the input argument, or that will first pad the input then apply a Conv2D
      layer.

    Raises:
      ValueError: if kernel size is not a pair of equal
        integers (representing a square kernel).
    """
    if not isinstance(kernel_size, tuple):
      raise ValueError('kernel is expected to be a tuple.')
    if len(kernel_size) != 2:
      raise ValueError('kernel is expected to be length two.')
    if kernel_size[0] != kernel_size[1]:
      raise ValueError('kernel is expected to be square.')
    layer_name = kwargs['name']
    if self._conv_defs:
      conv_filters = model_utils.get_conv_def(self._conv_defs, layer_name)
      if conv_filters:
        filters = conv_filters
    # Apply the width multiplier and the minimum depth to the convolution layers
    filters = int(filters * self._alpha)
    if self._min_depth and filters < self._min_depth:
      filters = self._min_depth

    if self._conv_hyperparams:
      kwargs = self._conv_hyperparams.params(**kwargs)
    else:
      kwargs['kernel_regularizer'] = self.regularizer
      kwargs['kernel_initializer'] = self.initializer

    kwargs['padding'] = 'same'
    if self._use_explicit_padding and kernel_size[0] > 1:
      kwargs['padding'] = 'valid'
      def padded_conv(features):  # pylint: disable=invalid-name
        padded_features = self._FixedPaddingLayer(kernel_size)(features)
        return tf.keras.layers.Conv2D(
            filters, kernel_size, **kwargs)(padded_features)
      return padded_conv
    else:
      return tf.keras.layers.Conv2D(filters, kernel_size, **kwargs)