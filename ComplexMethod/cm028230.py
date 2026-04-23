def __init__(self,
               is_training,
               depth_multiplier,
               min_depth,
               pad_to_multiple,
               conv_hyperparams,
               freeze_batchnorm,
               inplace_batchnorm_update,
               bifpn_min_level,
               bifpn_max_level,
               bifpn_num_iterations,
               bifpn_num_filters,
               bifpn_combine_method,
               efficientnet_version,
               use_explicit_padding=None,
               use_depthwise=None,
               use_native_resize_op=False,
               override_base_feature_extractor_hyperparams=None,
               name=None):
    """SSD Keras-based EfficientNetBiFPN (EfficientDet) feature extractor.

    Args:
      is_training: whether the network is in training mode.
      depth_multiplier: unsupported by EfficientNetBiFPN. float, depth
        multiplier for the feature extractor.
      min_depth: minimum feature extractor depth.
      pad_to_multiple: the nearest multiple to zero pad the input height and
        width dimensions to.
      conv_hyperparams: a `hyperparams_builder.KerasLayerHyperparams` object
        containing convolution hyperparameters for the layers added on top of
        the base feature extractor.
      freeze_batchnorm: whether to freeze batch norm parameters during training
        or not. When training with a small batch size (e.g. 1), it is desirable
        to freeze batch norm update and use pretrained batch norm params.
      inplace_batchnorm_update: whether to update batch norm moving average
        values inplace. When this is false train op must add a control
        dependency on tf.graphkeys.UPDATE_OPS collection in order to update
        batch norm statistics.
      bifpn_min_level: the highest resolution feature map to use in BiFPN. The
        valid values are {2, 3, 4, 5} which map to Resnet blocks {1, 2, 3, 4}
        respectively.
      bifpn_max_level: the smallest resolution feature map to use in the BiFPN.
        BiFPN constructions uses features maps starting from bifpn_min_level
        upto the bifpn_max_level. In the case that there are not enough feature
        maps in the backbone network, additional feature maps are created by
        applying stride 2 convolutions until we get the desired number of BiFPN
        levels.
      bifpn_num_iterations: number of BiFPN iterations. Overrided if
        efficientdet_version is provided.
      bifpn_num_filters: number of filters (channels) in all BiFPN layers.
        Overrided if efficientdet_version is provided.
      bifpn_combine_method: the method used to combine BiFPN nodes.
      efficientnet_version: the EfficientNet version to use for this feature
        extractor's backbone.
      use_explicit_padding: unsupported by EfficientNetBiFPN. Whether to use
        explicit padding when extracting features.
      use_depthwise: unsupported by EfficientNetBiFPN, since BiFPN uses regular
        convolutions when inputs to a node have a differing number of channels,
        and use separable convolutions after combine operations.
      use_native_resize_op: If True, will use
        tf.compat.v1.image.resize_nearest_neighbor for bifpn unsampling.
      override_base_feature_extractor_hyperparams: Whether to override the
        efficientnet backbone's default weight decay with the weight decay
        defined by `conv_hyperparams`. Note, only overriding of weight decay is
        currently supported.
      name: a string name scope to assign to the model. If 'None', Keras will
        auto-generate one from the class name.
    """
    super(SSDEfficientNetBiFPNKerasFeatureExtractor, self).__init__(
        is_training=is_training,
        depth_multiplier=depth_multiplier,
        min_depth=min_depth,
        pad_to_multiple=pad_to_multiple,
        conv_hyperparams=conv_hyperparams,
        freeze_batchnorm=freeze_batchnorm,
        inplace_batchnorm_update=inplace_batchnorm_update,
        use_explicit_padding=None,
        use_depthwise=None,
        override_base_feature_extractor_hyperparams=
        override_base_feature_extractor_hyperparams,
        name=name)
    if depth_multiplier != 1.0:
      raise ValueError('EfficientNetBiFPN does not support a non-default '
                       'depth_multiplier.')
    if use_explicit_padding:
      raise ValueError('EfficientNetBiFPN does not support explicit padding.')
    if use_depthwise:
      raise ValueError('EfficientNetBiFPN does not support use_depthwise.')

    self._bifpn_min_level = bifpn_min_level
    self._bifpn_max_level = bifpn_max_level
    self._bifpn_num_iterations = bifpn_num_iterations
    self._bifpn_num_filters = max(bifpn_num_filters, min_depth)
    self._bifpn_node_params = {'combine_method': bifpn_combine_method}
    self._efficientnet_version = efficientnet_version
    self._use_native_resize_op = use_native_resize_op

    logging.info('EfficientDet EfficientNet backbone version: %s',
                 self._efficientnet_version)
    logging.info('EfficientDet BiFPN num filters: %d', self._bifpn_num_filters)
    logging.info('EfficientDet BiFPN num iterations: %d',
                 self._bifpn_num_iterations)

    self._backbone_max_level = min(
        max(_EFFICIENTNET_LEVEL_ENDPOINTS.keys()), bifpn_max_level)
    self._output_layer_names = [
        _EFFICIENTNET_LEVEL_ENDPOINTS[i]
        for i in range(bifpn_min_level, self._backbone_max_level + 1)]
    self._output_layer_alias = [
        'level_{}'.format(i)
        for i in range(bifpn_min_level, self._backbone_max_level + 1)]

    # Initialize the EfficientNet backbone.
    # Note, this is currently done in the init method rather than in the build
    # method, since doing so introduces an error which is not well understood.
    efficientnet_overrides = {'rescale_input': False}
    if override_base_feature_extractor_hyperparams:
      efficientnet_overrides[
          'weight_decay'] = conv_hyperparams.get_regularizer_weight()
    if (conv_hyperparams.use_sync_batch_norm() and
        is_tpu_strategy(tf.distribute.get_strategy())):
      efficientnet_overrides['batch_norm'] = 'tpu'
    efficientnet_base = efficientnet_model.EfficientNet.from_name(
        model_name=self._efficientnet_version, overrides=efficientnet_overrides)
    outputs = [efficientnet_base.get_layer(output_layer_name).output
               for output_layer_name in self._output_layer_names]
    self._efficientnet = tf.keras.Model(
        inputs=efficientnet_base.inputs, outputs=outputs)
    self.classification_backbone = efficientnet_base
    self._bifpn_stage = None