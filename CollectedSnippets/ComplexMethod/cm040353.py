def _can_use_flash_attention(query, key, value, bias, raise_error=False):
    """Verify the availability of flash attention."""
    try:
        from jax._src.cudnn.fused_attention_stablehlo import _normalize_layout
        from jax._src.cudnn.fused_attention_stablehlo import (
            check_compute_capability,
        )
        from jax._src.cudnn.fused_attention_stablehlo import check_cudnn_version
        from jax._src.cudnn.fused_attention_stablehlo import (
            check_is_flash_attention,
        )
        from jax._src.cudnn.fused_attention_stablehlo import check_layout
        from jax.nn import dot_product_attention as dot_product_attention
    except ImportError:
        if raise_error:
            raise ImportError(
                "Flash attention is not supported in your current JAX version. "
                "Please update it by following the official guide: "
                "https://jax.readthedocs.io/en/latest/installation.html"
            )
        return False

    if jax.devices()[0].platform == "tpu":
        return True
    try:
        # Check if cuDNN is installed and raise RuntimeError if cuDNN is not
        # detected
        cudnn_version = check_cudnn_version()
        # Only support at least Ampere
        if not check_compute_capability("8.0"):
            raise RuntimeError("Require at least Ampere arch to run")

        # Inspect inputs of `check_layout`
        check_layout_params = list(
            inspect.signature(check_layout).parameters.keys()
        )
        for known_param in ("query", "key", "value", "bias", "layout"):
            check_layout_params.remove(known_param)
        # Defaults to `None` when not specified.
        check_layout_kwargs = {key: None for key in check_layout_params}
        check_layout(
            query,
            key,
            value,
            bias,
            layout=_normalize_layout("BTNH"),
            **check_layout_kwargs,
        )

        # Inspect inputs of `check_is_flash_attention`
        check_is_flash_attention_params = inspect.signature(
            check_is_flash_attention
        ).parameters
        check_is_flash_attention_kwargs = {
            "query": query,
            "key": key,
            "value": value,
            "layout": _normalize_layout("BTNH"),
            "cudnn_version": cudnn_version,
            "has_bias": bias is not None,
            "is_training": False,
        }
        # Remove unsupported arguments
        for param in list(check_is_flash_attention_kwargs.keys()):
            if param not in check_is_flash_attention_params:
                check_is_flash_attention_kwargs.pop(param)
        check_is_flash_attention(**check_is_flash_attention_kwargs)
        return True
    except:
        if raise_error:
            raise
        return False