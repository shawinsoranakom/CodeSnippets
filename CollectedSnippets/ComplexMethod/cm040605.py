def get_block_size_for_layer(layer, config):
    """Determine the block size for int4 quantization.

    The block size can be specified either through the `config` argument
    or through the `dtype_policy` if it is of type `Int4DTypePolicy`.

    The config argument is usually available when quantizing the layer
    via the `quantize` method. If the layer was deserialized from a
    saved model, the block size should be specified in the `dtype_policy`.

    Args:
        layer: The layer being quantized.
        config: An optional configuration object that may contain the
            `block_size` attribute.
    Returns:
        int or None. The determined block size for int4 quantization.
        Returns `None` or `-1` for per-channel quantization.
    """
    from keras.src.dtype_policies.dtype_policy import Int4DTypePolicy
    from keras.src.dtype_policies.dtype_policy_map import DTypePolicyMap

    if config and isinstance(config, Int4QuantizationConfig):
        return config.block_size
    elif isinstance(layer.dtype_policy, Int4DTypePolicy):
        block_size = layer.dtype_policy.block_size
        # Convert -1 to None for consistency
        return None if block_size == -1 else block_size
    elif isinstance(layer.dtype_policy, DTypePolicyMap):
        policy = layer.dtype_policy[layer.path]
        if isinstance(policy, Int4DTypePolicy):
            block_size = policy.block_size
            return None if block_size == -1 else block_size
        # Fall back to None for legacy QuantizedDTypePolicy
        return None
    else:
        # For backwards compatibility with models that don't have
        # Int4DTypePolicy (legacy per-channel mode)
        return None