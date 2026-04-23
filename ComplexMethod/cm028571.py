def call(self, inputs):
    """Forward pass of the segmentation head.

    It supports both a tuple of 2 tensors or 2 dictionaries. The first is
    backbone endpoints, and the second is decoder endpoints. When inputs are
    tensors, they are from a single level of feature maps. When inputs are
    dictionaries, they contain multiple levels of feature maps, where the key
    is the index of feature map.

    Args:
      inputs: A tuple of 2 feature map tensors of shape
        [batch, height_l, width_l, channels] or 2 dictionaries of tensors:
        - key: A `str` of the level of the multilevel features.
        - values: A `tf.Tensor` of the feature map tensors, whose shape is
            [batch, height_l, width_l, channels].
        The first is backbone endpoints, and the second is decoder endpoints.
    Returns:
      segmentation prediction mask: A `tf.Tensor` of the segmentation mask
        scores predicted from input features.
    """

    backbone_output = inputs[0]
    decoder_output = inputs[1]
    if self._config_dict['feature_fusion'] in {'deeplabv3plus',
                                               'deeplabv3plus_sum_to_merge'}:
      # deeplabv3+ feature fusion
      x = decoder_output[str(self._config_dict['level'])] if isinstance(
          decoder_output, dict) else decoder_output
      y = backbone_output[str(self._config_dict['low_level'])] if isinstance(
          backbone_output, dict) else backbone_output
      y = self._dlv3p_norm(self._dlv3p_conv(y))
      y = self._activation(y)

      x = tf.image.resize(
          x, tf.shape(y)[1:3], method=tf.image.ResizeMethod.BILINEAR)
      x = tf.cast(x, dtype=y.dtype)
      if self._config_dict['feature_fusion'] == 'deeplabv3plus':
        x = tf.concat([x, y], axis=self._bn_axis)
      else:
        x = tf_keras.layers.Add()([x, y])
    elif self._config_dict['feature_fusion'] == 'pyramid_fusion':
      if not isinstance(decoder_output, dict):
        raise ValueError('Only support dictionary decoder_output.')
      x = nn_layers.pyramid_feature_fusion(decoder_output,
                                           self._config_dict['level'])
    elif self._config_dict['feature_fusion'] == 'panoptic_fpn_fusion':
      x = self._panoptic_fpn_fusion(decoder_output)
    else:
      x = decoder_output[str(self._config_dict['level'])] if isinstance(
          decoder_output, dict) else decoder_output

    for conv, norm in zip(self._convs, self._norms):
      x = conv(x)
      x = norm(x)
      x = self._activation(x)
    if self._config_dict['upsample_factor'] > 1:
      x = spatial_transform_ops.nearest_upsampling(
          x, scale=self._config_dict['upsample_factor'])

    return self._classifier(x)