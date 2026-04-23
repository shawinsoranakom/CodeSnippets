def adapt_config_dict(
    config_dict: dict[str, Any],
    defaults: dict[str, Any],
) -> PretrainedConfig:
    config_dict = _remap_general_mistral_args(config_dict)
    config_dict = _remap_mistral_sliding_window(config_dict)

    if bool(config_dict.get("quantization")):
        config_dict = _remap_mistral_quantization_args(config_dict)

    is_mla = bool(config_dict.get("qk_nope_head_dim"))
    if is_mla:
        config_dict = _remap_mistral_mla_args(config_dict)

    is_moe = bool(config_dict.get("moe"))
    is_mistral_large_3 = (
        is_moe and (config_dict["moe"].get("num_shared_experts") or 0) > 0
    )
    if config_dict.get("model_type") == "mamba":
        config_dict["architectures"] = ["Mamba2ForCausalLM"]
    elif is_moe and is_mistral_large_3:
        config_dict = _remap_moe_args(config_dict)
        config_dict["model_type"] = "deepseek_v3"
        config_dict["architectures"] = ["MistralLarge3ForCausalLM"]

        assert "llama_4_scaling" in config_dict, (
            "MistralLarge3 expect llama4 scaling config."
        )
        llama_4_scaling_config_keys = ["original_max_position_embeddings", "beta"]
        assert all(
            [
                key in config_dict["llama_4_scaling"]
                for key in llama_4_scaling_config_keys
            ]
        ), (
            "llama_4_scaling config should define the keys: "
            f"{','.join(llama_4_scaling_config_keys)}"
        )
    elif is_moe:
        config_dict["architectures"] = ["MixtralForCausalLM"]
    else:
        config_dict["architectures"] = ["MistralForCausalLM"]

    if bool(config_dict.get("yarn")):
        config_dict = _remap_mistral_yarn_args(config_dict)

    if bool(config_dict.get("llama_4_scaling")):
        llama_4_scaling_config_keys = ["original_max_position_embeddings", "beta"]
        assert all(
            [
                key in config_dict["llama_4_scaling"]
                for key in llama_4_scaling_config_keys
            ]
        ), (
            "llama_4_scaling config should define the keys: "
            f"{','.join(llama_4_scaling_config_keys)}"
        )

    is_vision = (config_dict.get("multimodal") or {}).get(
        "vision_encoder_args"
    ) or config_dict.get("vision_encoder")
    is_audio = bool(
        ((config_dict.get("multimodal") or {}).get("whisper_model_args") or {}).get(
            "encoder_args"
        )
    )

    assert not (is_vision and is_audio), "Vision and audio are mutually exclusive"

    if is_vision:
        config_dict = _remap_mistral_vision_args(config_dict)
    if is_audio:
        config_dict = _remap_mistral_audio_args(config_dict)

    for k, v in defaults.items():
        config_dict.setdefault(k, v)

    config = PretrainedConfig.from_dict(config_dict)

    logger.debug("Initialized config %s", config)

    return config