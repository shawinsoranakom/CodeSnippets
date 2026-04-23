def __call__(self, multilevel_features, is_training=None):
    """Returns the FPN features for a given multilevel features.

    Args:
      multilevel_features: a `dict` containing `int` keys for continuous feature
        levels, e.g., [2, 3, 4, 5]. The values are corresponding features with
        shape [batch_size, height_l, width_l, num_filters].
      is_training: `bool` if True, the model is in training mode.

    Returns:
      a `dict` containing `int` keys for continuous feature levels
      [min_level, min_level + 1, ..., max_level]. The values are corresponding
      FPN features with shape [batch_size, height_l, width_l, fpn_feat_dims].
    """
    input_levels = list(multilevel_features.keys())
    if min(input_levels) > self._min_level:
      raise ValueError(
          'The minimum backbone level %d should be '%(min(input_levels)) +
          'less or equal to FPN minimum level %d.:'%(self._min_level))
    backbone_max_level = min(max(input_levels), self._max_level)
    with tf.name_scope('fpn'):
      # Adds lateral connections.
      feats_lateral = {}
      for level in range(self._min_level, backbone_max_level + 1):
        feats_lateral[level] = self._lateral_conv2d_op[level](
            multilevel_features[level])

      # Adds top-down path.
      feats = {backbone_max_level: feats_lateral[backbone_max_level]}
      for level in range(backbone_max_level - 1, self._min_level - 1, -1):
        feats[level] = spatial_transform_ops.nearest_upsampling(
            feats[level + 1], 2) + feats_lateral[level]

      # Adds post-hoc 3x3 convolution kernel.
      for level in range(self._min_level, backbone_max_level + 1):
        feats[level] = self._post_hoc_conv2d_op[level](feats[level])

      # Adds coarser FPN levels introduced for RetinaNet.
      for level in range(backbone_max_level + 1, self._max_level + 1):
        feats_in = feats[level - 1]
        if level > backbone_max_level + 1:
          feats_in = self._activation_op(feats_in)
        feats[level] = self._coarse_conv2d_op[level](feats_in)
      if self._use_batch_norm:
        # Adds batch_norm layer.
        for level in range(self._min_level, self._max_level + 1):
          feats[level] = self._norm_activations[level](
              feats[level], is_training=is_training)
    return feats