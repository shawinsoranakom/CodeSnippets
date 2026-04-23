def get_kv_cache_quant_algo_string(quant_cfg: dict[str, Any]) -> str | None:
    """Get the KV cache quantization algorithm string from the quantization config.

    Maps various FP8 format names to vLLM's standard cache dtype strings.
    Returns None if no kv_cache_quant_algo is specified.
    Returns "auto" if the value is not recognized/supported.
    """
    # Mapping from model config values to vLLM cache_dtype strings

    quant_method = quant_cfg.get("quant_method", "")
    if quant_method.startswith("modelopt"):
        quantization_inner = quant_cfg.get("quantization", quant_cfg)
        # Check if quant config is specified and use kv cache quant algo
        kv_algo = (
            quantization_inner.get("kv_cache_scheme")
            or quant_cfg.get("kv_cache_scheme")
            or quantization_inner.get("kv_cache_quant_algo")
            or quant_cfg.get("kv_cache_quant_algo")
        )
        if isinstance(kv_algo, dict):
            if (
                kv_algo.get("dynamic") is False
                and kv_algo.get("num_bits") == 8
                and kv_algo.get("type") == "float"
            ):
                kv_algo = "fp8"
            elif kv_algo.get("num_bits") == 4 and kv_algo.get("type") == "float":
                kv_algo = "nvfp4"
            else:
                # Unknown/unsupported format - return "auto" as safe fallback
                logger.warning(
                    "WARNING: Unknown kv_cache_quant_algo '%s' in model "
                    "config. Supported values: %s. Falling back to 'auto'.",
                    f"{kv_algo}",
                    list(MODELOPT_TO_VLLM_KV_CACHE_DTYPE_MAP.keys()),
                )
                return "auto"
        if isinstance(kv_algo, str):
            kv_algo_lower = kv_algo.lower()

            # Try to map to vLLM's standard format
            if kv_algo_lower in MODELOPT_TO_VLLM_KV_CACHE_DTYPE_MAP:
                return MODELOPT_TO_VLLM_KV_CACHE_DTYPE_MAP[kv_algo_lower]
            else:
                # Unknown/unsupported format - return "auto" as safe fallback
                logger.warning(
                    "WARNING: Unknown kv_cache_quant_algo '%s' in model "
                    "config. Supported values: %s. Falling back to 'auto'.",
                    kv_algo,
                    list(MODELOPT_TO_VLLM_KV_CACHE_DTYPE_MAP.keys()),
                )
                return "auto"
    return None