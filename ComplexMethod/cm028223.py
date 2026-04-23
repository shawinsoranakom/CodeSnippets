def __init__(self, resnet_type, channel_means=(0., 0., 0.),
               channel_stds=(1., 1., 1.), bgr_ordering=False):
    """Initializes the feature extractor with a specific ResNet architecture.

    Args:
      resnet_type: A string specifying which kind of ResNet to use. Currently
        only `resnet_v1_50` and `resnet_v1_101` are supported.
      channel_means: A tuple of floats, denoting the mean of each channel
        which will be subtracted from it.
      channel_stds: A tuple of floats, denoting the standard deviation of each
        channel. Each channel will be divided by its standard deviation value.
      bgr_ordering: bool, if set will change the channel ordering to be in the
        [blue, red, green] order.

    """

    super(CenterNetResnetV1FpnFeatureExtractor, self).__init__(
        channel_means=channel_means, channel_stds=channel_stds,
        bgr_ordering=bgr_ordering)
    if resnet_type == 'resnet_v1_50':
      self._base_model = tf.keras.applications.ResNet50(weights=None,
                                                        include_top=False)
    elif resnet_type == 'resnet_v1_101':
      self._base_model = tf.keras.applications.ResNet101(weights=None,
                                                         include_top=False)
    elif resnet_type == 'resnet_v1_18':
      self._base_model = resnet_v1.resnet_v1_18(weights=None, include_top=False)
    elif resnet_type == 'resnet_v1_34':
      self._base_model = resnet_v1.resnet_v1_34(weights=None, include_top=False)
    else:
      raise ValueError('Unknown Resnet Model {}'.format(resnet_type))
    output_layers = _RESNET_MODEL_OUTPUT_LAYERS[resnet_type]
    outputs = [self._base_model.get_layer(output_layer_name).output
               for output_layer_name in output_layers]

    self._resnet_model = tf.keras.models.Model(inputs=self._base_model.input,
                                               outputs=outputs)
    resnet_outputs = self._resnet_model(self._base_model.input)

    # Construct the top-down feature maps.
    top_layer = resnet_outputs[-1]
    residual_op = tf.keras.layers.Conv2D(filters=256, kernel_size=1,
                                         strides=1, padding='same')
    top_down = residual_op(top_layer)

    num_filters_list = [256, 128, 64]
    for i, num_filters in enumerate(num_filters_list):
      level_ind = 2 - i
      # Upsample.
      upsample_op = tf.keras.layers.UpSampling2D(2, interpolation='nearest')
      top_down = upsample_op(top_down)

      # Residual (skip-connection) from bottom-up pathway.
      residual_op = tf.keras.layers.Conv2D(filters=num_filters, kernel_size=1,
                                           strides=1, padding='same')
      residual = residual_op(resnet_outputs[level_ind])

      # Merge.
      top_down = top_down + residual
      next_num_filters = num_filters_list[i+1] if i + 1 <= 2 else 64
      conv = tf.keras.layers.Conv2D(filters=next_num_filters,
                                    kernel_size=3, strides=1, padding='same')
      top_down = conv(top_down)
      top_down = tf.keras.layers.BatchNormalization()(top_down)
      top_down = tf.keras.layers.ReLU()(top_down)

    self._feature_extractor_model = tf.keras.models.Model(
        inputs=self._base_model.input, outputs=top_down)