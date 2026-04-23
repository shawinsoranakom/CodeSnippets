def _build_ssd_feature_extractor(feature_extractor_config,
                                 is_training,
                                 freeze_batchnorm,
                                 reuse_weights=None):
  """Builds a ssd_meta_arch.SSDFeatureExtractor based on config.

  Args:
    feature_extractor_config: A SSDFeatureExtractor proto config from ssd.proto.
    is_training: True if this feature extractor is being built for training.
    freeze_batchnorm: Whether to freeze batch norm parameters during
      training or not. When training with a small batch size (e.g. 1), it is
      desirable to freeze batch norm update and use pretrained batch norm
      params.
    reuse_weights: if the feature extractor should reuse weights.

  Returns:
    ssd_meta_arch.SSDFeatureExtractor based on config.

  Raises:
    ValueError: On invalid feature extractor type.
  """
  feature_type = feature_extractor_config.type
  depth_multiplier = feature_extractor_config.depth_multiplier
  min_depth = feature_extractor_config.min_depth
  pad_to_multiple = feature_extractor_config.pad_to_multiple
  use_explicit_padding = feature_extractor_config.use_explicit_padding
  use_depthwise = feature_extractor_config.use_depthwise

  is_keras = tf_version.is_tf2()
  if is_keras:
    conv_hyperparams = hyperparams_builder.KerasLayerHyperparams(
        feature_extractor_config.conv_hyperparams)
  else:
    conv_hyperparams = hyperparams_builder.build(
        feature_extractor_config.conv_hyperparams, is_training)
  override_base_feature_extractor_hyperparams = (
      feature_extractor_config.override_base_feature_extractor_hyperparams)

  if not is_keras and feature_type not in SSD_FEATURE_EXTRACTOR_CLASS_MAP:
    raise ValueError('Unknown ssd feature_extractor: {}'.format(feature_type))

  if is_keras:
    feature_extractor_class = SSD_KERAS_FEATURE_EXTRACTOR_CLASS_MAP[
        feature_type]
  else:
    feature_extractor_class = SSD_FEATURE_EXTRACTOR_CLASS_MAP[feature_type]
  kwargs = {
      'is_training':
          is_training,
      'depth_multiplier':
          depth_multiplier,
      'min_depth':
          min_depth,
      'pad_to_multiple':
          pad_to_multiple,
      'use_explicit_padding':
          use_explicit_padding,
      'use_depthwise':
          use_depthwise,
      'override_base_feature_extractor_hyperparams':
          override_base_feature_extractor_hyperparams
  }

  if feature_extractor_config.HasField('replace_preprocessor_with_placeholder'):
    kwargs.update({
        'replace_preprocessor_with_placeholder':
            feature_extractor_config.replace_preprocessor_with_placeholder
    })

  if feature_extractor_config.HasField('num_layers'):
    kwargs.update({'num_layers': feature_extractor_config.num_layers})

  if is_keras:
    kwargs.update({
        'conv_hyperparams': conv_hyperparams,
        'inplace_batchnorm_update': False,
        'freeze_batchnorm': freeze_batchnorm
    })
  else:
    kwargs.update({
        'conv_hyperparams_fn': conv_hyperparams,
        'reuse_weights': reuse_weights,
    })


  if feature_extractor_config.HasField('spaghettinet_arch_name'):
    kwargs.update({
        'spaghettinet_arch_name':
            feature_extractor_config.spaghettinet_arch_name,
    })

  if feature_extractor_config.HasField('fpn'):
    kwargs.update({
        'fpn_min_level':
            feature_extractor_config.fpn.min_level,
        'fpn_max_level':
            feature_extractor_config.fpn.max_level,
        'additional_layer_depth':
            feature_extractor_config.fpn.additional_layer_depth,
    })

  if feature_extractor_config.HasField('bifpn'):
    kwargs.update({
        'bifpn_min_level':
            feature_extractor_config.bifpn.min_level,
        'bifpn_max_level':
            feature_extractor_config.bifpn.max_level,
        'bifpn_num_iterations':
            feature_extractor_config.bifpn.num_iterations,
        'bifpn_num_filters':
            feature_extractor_config.bifpn.num_filters,
        'bifpn_combine_method':
            feature_extractor_config.bifpn.combine_method,
        'use_native_resize_op':
            feature_extractor_config.bifpn.use_native_resize_op,
    })

  return feature_extractor_class(**kwargs)