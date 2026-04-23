def call(self, feat, training, all_feats):
    hwc_idx = (2, 3, 1) if self.data_format == 'channels_first' else (1, 2, 3)
    height, width, num_channels = [feat.shape.as_list()[i] for i in hwc_idx]
    if all_feats:
      target_feat_shape = all_feats[self.feat_level].shape.as_list()
      target_height, target_width, _ = [target_feat_shape[i] for i in hwc_idx]
    else:
      # Default to downsampling if all_feats is empty.
      target_height, target_width = (height + 1) // 2, (width + 1) // 2

    # If conv_after_downsample is True, when downsampling, apply 1x1 after
    # downsampling for efficiency.
    if height > target_height and width > target_width:
      if not self.conv_after_downsample:
        feat = self._maybe_apply_1x1(feat, training, num_channels)
      feat = self._pool2d(feat, height, width, target_height, target_width)
      if self.conv_after_downsample:
        feat = self._maybe_apply_1x1(feat, training, num_channels)
    elif height <= target_height and width <= target_width:
      feat = self._maybe_apply_1x1(feat, training, num_channels)
      if height < target_height or width < target_width:
        feat = self._upsample2d(feat, target_height, target_width, training)
    else:
      raise ValueError(
          'Incompatible Resampling : feat shape {}x{} target_shape: {}x{}'
          .format(height, width, target_height, target_width))

    return feat