def dummy_hf_overrides(
    hf_config: PretrainedConfig,
    *,
    model_arch: str = "",
    exist_overrides: dict[str, Any] | None = None,
    use_original_num_layers: bool = False,
) -> PretrainedConfig:
    """
    Dummy HF overrides function used to create dummy model
    with only minimum nums of layer.
    """
    # Copy because this helper is called more than once
    # while loading config, and we `.pop()`
    exist_overrides = (exist_overrides or {}).copy()
    text_config_override = exist_overrides.pop("text_config", None)
    hf_config.update(exist_overrides)

    text_config = hf_config.get_text_config()
    if text_config_override is not None:
        # multimodal test models may override *some* text-model fields
        text_config.update(text_config_override)

    # Ensure at least 2 expert per group
    # Since `grouped_topk` assumes top-2
    n_group = getattr(text_config, "n_group", None)
    # Kimi uses `num_expert_group` instead of `n_group`.
    if n_group is None:
        n_group = getattr(text_config, "num_expert_group", None)
    num_experts = n_group * 2 if n_group is not None else 2

    # we use three layers for Gemma-3n to check
    # both normal layer and kv_shared_layer
    if use_original_num_layers:
        # Use the original number of layers from the config
        num_layers = getattr(text_config, "num_layers", 1)
        num_hidden_layers = getattr(text_config, "num_hidden_layers", 1)
    else:
        # Use minimal layers for testing
        num_layers = 1
        num_hidden_layers = (
            3
            if model_arch
            in (
                "Gemma3nForConditionalGeneration",
                "Gemma4ForCausalLM",
                "Gemma4ForConditionalGeneration",
            )
            else 1
        )

    update_dict = {
        "num_layers": num_layers,
        # For Gemma-3n
        "num_kv_shared_layers": 1,
    }

    _hf_config = hf_config

    class DummyConfig:
        hf_config = _hf_config
        hf_text_config = text_config

    model_arch_config = ModelConfig.get_model_arch_config(DummyConfig)
    # Only set MoE related config when the model has MoE layers.
    # Otherwise all models detected as MoE by _get_transformers_backend_cls.
    if model_arch_config.num_experts > 0:
        update_dict.update(
            {
                "num_experts": num_experts,
                "num_experts_per_tok": 2,
                # Kimi uses `num_experts_per_token`.
                "num_experts_per_token": 2,
                "num_local_experts": num_experts,
                # Otherwise there will not be any expert layers
                "first_k_dense_replace": 0,
                # To avoid OOM on DeepSeek-V3
                "n_routed_experts": num_experts,
            }
        )

    # Update num_hidden_layers for non-Longcat architectures
    if model_arch != "LongcatFlashForCausalLM" and model_arch != "LongCatFlashMTPModel":
        update_dict["num_hidden_layers"] = num_hidden_layers

    text_config.update(update_dict)

    if hasattr(hf_config, "vision_config"):
        hf_config.vision_config.update(
            {
                "num_layers": 1,
                "num_hidden_layers": 1,
            }
        )

    # e.g.: ibm-granite/granite-speech-3.3-2b
    if hasattr(hf_config, "encoder_config"):
        hf_config.encoder_config.update(
            {
                "num_layers": 1,
                "num_hidden_layers": 1,
            }
        )

    # e.g.: Qwen/Qwen2-Audio-7B-Instruct
    if hasattr(hf_config, "audio_config"):
        hf_config.audio_config.update(
            {
                "num_layers": 1,
                "num_hidden_layers": 1,
                "encoder_layers": 1,
            }
        )

    return hf_config