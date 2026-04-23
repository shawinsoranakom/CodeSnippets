def get_layer_class(use_attention, use_autoregression):
  """A convenience function to get a layer class based on requirements.

  Args:
    use_attention: if True a returned class will use attention.
    use_autoregression: if True a returned class will use auto regression.

  Returns:
    One of available sequence layers (child classes for SequenceLayerBase).
  """
  if use_attention and use_autoregression:
    layer_class = AttentionWithAutoregression
  elif use_attention and not use_autoregression:
    layer_class = Attention
  elif not use_attention and not use_autoregression:
    layer_class = NetSlice
  elif not use_attention and use_autoregression:
    layer_class = NetSliceWithAutoregression
  else:
    raise AssertionError('Unsupported sequence layer class')

  logging.debug('Use %s as a layer class', layer_class.__name__)
  return layer_class