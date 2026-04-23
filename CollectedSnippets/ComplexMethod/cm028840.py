def _build_model(self, inputs):
    """Builds model architecture.

    Args:
      inputs: the keras input spec.

    Returns:
      endpoints: A dictionary of backbone endpoint features.
    """
    # Build stem.
    x = self._build_stem(inputs, stem_type=self._stem_type)

    temporal_kernel_size = 1 if self._stem_pool_temporal_stride == 1 else 3
    x = layers.MaxPool3D(
        pool_size=[temporal_kernel_size, 3, 3],
        strides=[self._stem_pool_temporal_stride, 2, 2],
        padding='same')(x)

    # Build intermediate blocks and endpoints.
    resnet_specs = RESNET_SPECS[self._model_id]
    if len(self._temporal_strides) != len(resnet_specs) or len(
        self._temporal_kernel_sizes) != len(resnet_specs):
      raise ValueError(
          'Number of blocks in temporal specs should equal to resnet_specs.')

    endpoints = {}
    for i, resnet_spec in enumerate(resnet_specs):
      if resnet_spec[0] == 'bottleneck3d':
        block_fn = nn_blocks_3d.BottleneckBlock3D
      else:
        raise ValueError('Block fn `{}` is not supported.'.format(
            resnet_spec[0]))

      use_self_gating = (
          self._use_self_gating[i] if self._use_self_gating else False)
      x = self._block_group(
          inputs=x,
          filters=resnet_spec[1],
          temporal_kernel_sizes=self._temporal_kernel_sizes[i],
          temporal_strides=self._temporal_strides[i],
          spatial_strides=(1 if i == 0 else 2),
          block_fn=block_fn,
          block_repeats=resnet_spec[2],
          stochastic_depth_drop_rate=nn_layers.get_stochastic_depth_rate(
              self._init_stochastic_depth_rate, i + 2, 5),
          use_self_gating=use_self_gating,
          name='block_group_l{}'.format(i + 2))
      endpoints[str(i + 2)] = x

    return endpoints