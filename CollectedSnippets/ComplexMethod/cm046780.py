def estimate_fp16_model_size_bytes(
    model_name: str, hf_token: Optional[str] = None
) -> tuple[Optional[int], str]:
    estimate_model = _resolve_model_identifier_for_gpu_estimate(
        model_name, hf_token = hf_token
    )

    total_params = None
    if "/" in estimate_model and not Path(estimate_model).exists():
        total_params = _get_hf_safetensors_total_params(
            estimate_model, hf_token = hf_token
        )
    if total_params:
        return int(total_params * 2), "safetensors"

    config = _load_config_for_gpu_estimate(estimate_model, hf_token = hf_token)
    if config is not None:
        config_bytes = _estimate_fp16_model_size_bytes_from_config(config)
        if config_bytes is not None:
            return config_bytes, "config"

    local_bytes = _get_local_weight_size_bytes(estimate_model)
    if local_bytes is not None:
        return local_bytes, "weight_bytes"

    vllm_bytes = _estimate_fp16_model_size_bytes_from_vllm_utils(config)
    if vllm_bytes is not None:
        return vllm_bytes, "vllm_utils"

    return None, "unavailable"