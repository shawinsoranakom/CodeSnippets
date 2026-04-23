def get_quantization_group_size(config) -> int | None:
    """Extract the quantization group size from the HF model config.

    This reads directly from the HuggingFace config object (as returned by
    ``get_config()``), not from vLLM's quantization config classes.

    Supports AWQ/GPTQ-style configs (direct 'group_size' key) and
    compressed-tensors configs (nested inside 'config_groups').
    """
    quantization_config = getattr(config, "quantization_config", {})
    if not isinstance(quantization_config, dict):
        return None
    # AWQ / GPTQ style: group_size is a top-level key
    gs = quantization_config.get("group_size")
    if gs is not None:
        return gs
    # compressed-tensors style: group_size is nested in config_groups
    config_groups = quantization_config.get("config_groups", {})
    if not isinstance(config_groups, dict):
        return None
    for group_cfg in config_groups.values():
        if not isinstance(group_cfg, dict):
            continue
        weights = group_cfg.get("weights", {})
        if not isinstance(weights, dict):
            continue
        gs = weights.get("group_size")
        if gs is not None:
            return gs
    return None