def _get_cache_dict(cache: DynamicCache):
    """Convert cache to dictionary format for pytree operations."""
    if any(not isinstance(layer, (DynamicLayer, DynamicSlidingWindowLayer)) for layer in cache.layers):
        raise RuntimeError("This pytree flattening function should only be applied to DynamicCache")

    if not is_torch_greater_or_equal_than_2_6:
        logging.warning("DynamicCache + torch.export is tested on torch 2.6.0+ and may not work on earlier versions.")

    return {
        "key_cache": [layer.keys for layer in cache.layers if layer.keys is not None],
        "value_cache": [layer.values for layer in cache.layers if layer.values is not None],
    }