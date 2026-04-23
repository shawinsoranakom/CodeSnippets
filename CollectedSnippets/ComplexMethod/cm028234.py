def Conv2D(self, filters, kernel_size, **kwargs):
    """Builds a Conv2D layer according to the current Object Detection config.

    Overrides the Keras InceptionResnetV2 application's convolutions with ones
    that follow the spec specified by the Object Detection hyperparameters.

    If feature map alignment is enabled, the padding will be forced to 'same'.
    If output_stride is 8, some conv2d layers will be matched according to
    their name or filter counts or pre-alignment padding parameters, and will
    have the correct 'dilation rate' or 'strides' set.

    Args:
      filters: The number of filters to use for the convolution.
      kernel_size: The kernel size to specify the height and width of the 2D
        convolution window.
      **kwargs: Keyword args specified by the Keras application for
        constructing the convolution.

    Returns:
      A Keras Conv2D layer specified by the Object Detection hyperparameter
      configurations.
    """
    kwargs['kernel_regularizer'] = self.regularizer
    kwargs['bias_regularizer'] = self.regularizer

    # Because the Keras application does not set explicit names for most layers,
    # (instead allowing names to auto-increment), we must match individual
    # layers in the model according to their filter count, name, or
    # pre-alignment mapping. This means we can only align the feature maps
    # after we have applied our updates in cases where output_stride=8.
    if self._use_atrous and (filters == 384):
      kwargs['strides'] = 1

    name = kwargs.get('name')
    if self._use_atrous and (
        (name and 'block17' in name) or
        (filters == 128 or filters == 160 or
         (filters == 192 and kwargs.get('padding', '').lower() != 'valid'))):
      kwargs['dilation_rate'] = 2

    if self._align_feature_maps:
      kwargs['padding'] = 'same'

    return tf.keras.layers.Conv2D(filters, kernel_size, **kwargs)