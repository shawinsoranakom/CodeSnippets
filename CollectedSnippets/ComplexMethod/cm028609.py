def call(self, inputs: Tuple[Union[tf.Tensor, Mapping[str, tf.Tensor]],
                               Union[tf.Tensor, Mapping[str, tf.Tensor]]]):
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

    Returns:
      segmentation prediction mask: A `tf.Tensor` of the segmentation mask
        scores predicted from input features.
    """
    if self._config_dict['feature_fusion'] in (
        FeatureFusion.PYRAMID_FUSION, FeatureFusion.PANOPTIC_FPN_FUSION):
      raise ValueError(
          'The feature fusion method `pyramid_fusion` is not supported in QAT.')

    backbone_output = inputs[0]
    decoder_output = inputs[1]
    if self._config_dict['feature_fusion'] in {
        FeatureFusion.DEEPLABV3PLUS, FeatureFusion.DEEPLABV3PLUS_SUM_TO_MERGE
    }:
      # deeplabv3+ feature fusion.
      x = decoder_output[str(self._config_dict['level'])] if isinstance(
          decoder_output, dict) else decoder_output
      y = backbone_output[str(self._config_dict['low_level'])] if isinstance(
          backbone_output, dict) else backbone_output
      y = self._dlv3p_norm(self._dlv3p_conv(y))
      y = self._activation_layer(y)
      x = self._resizing_layer(x)
      x = tf.cast(x, dtype=y.dtype)
      if self._config_dict['feature_fusion'] == FeatureFusion.DEEPLABV3PLUS:
        x = self._concat_layer([x, y])
      else:
        x = self._add_layer([x, y])
    else:
      x = decoder_output[str(self._config_dict['level'])] if isinstance(
          decoder_output, dict) else decoder_output

    for conv, norm in zip(self._convs, self._norms):
      x = conv(x)
      x = norm(x)
      x = self._activation_layer(x)
    if self._config_dict['upsample_factor'] > 1:
      # Use keras layer for nearest upsampling so it is QAT compatible.
      x = self._upsampling_layer(x)

    return self._classifier(x)