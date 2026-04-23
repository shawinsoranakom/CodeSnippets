def extract_features(self, preprocessed_inputs):
    """Extract features from preprocessed inputs.

    Args:
      preprocessed_inputs: a [batch, height, width, channels] float tensor
        representing a batch of images.

    Returns:
      feature_maps: a list of tensors where the ith tensor has shape
        [batch, height_i, width_i, depth_i]
    """
    preprocessed_inputs = shape_utils.check_min_image_dim(
        33, preprocessed_inputs)

    with tf.variable_scope('MobilenetV2', reuse=self._reuse_weights) as scope:
      with slim.arg_scope(
          mobilenet_v2.training_scope(is_training=None, bn_decay=0.9997)), \
          slim.arg_scope(
              [mobilenet.depth_multiplier], min_depth=self._min_depth):
        with (slim.arg_scope(self._conv_hyperparams_fn())
              if self._override_base_feature_extractor_hyperparams else
              context_manager.IdentityContextManager()):
          _, image_features = mobilenet_v2.mobilenet_base(
              ops.pad_to_multiple(preprocessed_inputs, self._pad_to_multiple),
              final_endpoint='layer_19',
              depth_multiplier=self._depth_multiplier,
              conv_defs=self._conv_defs,
              use_explicit_padding=self._use_explicit_padding,
              scope=scope)
      depth_fn = lambda d: max(int(d * self._depth_multiplier), self._min_depth)
      with slim.arg_scope(self._conv_hyperparams_fn()):
        with tf.variable_scope('fpn', reuse=self._reuse_weights):
          feature_blocks = [
              'layer_4', 'layer_7', 'layer_14', 'layer_19'
          ]
          base_fpn_max_level = min(self._fpn_max_level, 5)
          feature_block_list = []
          for level in range(self._fpn_min_level, base_fpn_max_level + 1):
            feature_block_list.append(feature_blocks[level - 2])
          fpn_features = feature_map_generators.fpn_top_down_feature_maps(
              [(key, image_features[key]) for key in feature_block_list],
              depth=depth_fn(self._additional_layer_depth),
              use_depthwise=self._use_depthwise,
              use_explicit_padding=self._use_explicit_padding,
              use_native_resize_op=self._use_native_resize_op)
          feature_maps = []
          for level in range(self._fpn_min_level, base_fpn_max_level + 1):
            feature_maps.append(fpn_features['top_down_{}'.format(
                feature_blocks[level - 2])])
          last_feature_map = fpn_features['top_down_{}'.format(
              feature_blocks[base_fpn_max_level - 2])]
          # Construct coarse features
          padding = 'VALID' if self._use_explicit_padding else 'SAME'
          kernel_size = 3
          for i in range(base_fpn_max_level + 1, self._fpn_max_level + 1):
            if self._use_depthwise:
              conv_op = functools.partial(
                  slim.separable_conv2d, depth_multiplier=1)
            else:
              conv_op = slim.conv2d
            if self._use_explicit_padding:
              last_feature_map = ops.fixed_padding(
                  last_feature_map, kernel_size)
            last_feature_map = conv_op(
                last_feature_map,
                num_outputs=depth_fn(self._additional_layer_depth),
                kernel_size=[kernel_size, kernel_size],
                stride=2,
                padding=padding,
                scope='bottom_up_Conv2d_{}'.format(i - base_fpn_max_level + 19))
            feature_maps.append(last_feature_map)
    return feature_maps