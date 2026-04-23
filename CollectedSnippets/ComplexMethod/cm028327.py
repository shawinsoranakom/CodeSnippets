def _get_deepmac_network_by_type(name, num_init_channels, mask_size=None):
  """Get DeepMAC network model given a string type."""

  if name.startswith('hourglass'):
    if name == 'hourglass10':
      return hourglass_network.hourglass_10(num_init_channels,
                                            initial_downsample=False)
    elif name == 'hourglass20':
      return hourglass_network.hourglass_20(num_init_channels,
                                            initial_downsample=False)
    elif name == 'hourglass32':
      return hourglass_network.hourglass_32(num_init_channels,
                                            initial_downsample=False)
    elif name == 'hourglass52':
      return hourglass_network.hourglass_52(num_init_channels,
                                            initial_downsample=False)
    elif name == 'hourglass100':
      return hourglass_network.hourglass_100(num_init_channels,
                                             initial_downsample=False)
    elif name == 'hourglass20_uniform_size':
      return hourglass_network.hourglass_20_uniform_size(num_init_channels)

    elif name == 'hourglass20_no_shortcut':
      return hourglass_network.hourglass_20_no_shortcut(num_init_channels)

  elif name == 'fully_connected':
    if not mask_size:
      raise ValueError('Mask size must be set.')
    return FullyConnectedMaskHead(num_init_channels, mask_size)

  elif _is_mask_head_param_free(name):
    return tf.keras.layers.Lambda(lambda x: x)

  elif name.startswith('resnet'):
    return ResNetMaskNetwork(name, num_init_channels)

  raise ValueError('Unknown network type {}'.format(name))