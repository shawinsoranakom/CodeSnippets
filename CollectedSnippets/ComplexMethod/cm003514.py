def convert_config(
    original_config: dict,
    max_position_embeddings: int = 1_048_576,
    is_vision: bool = True,
    output_fp8: bool = True,
) -> Mistral3Config | Mistral4Config:
    r"""Convert original Mistral `params.json` to a HF config object."""
    original_vision_config = original_config.pop("vision_encoder", None)
    assert is_vision == (original_vision_config is not None)

    text_kwargs: dict[str, Any] = {
        "hidden_size": original_config["dim"],
        "num_hidden_layers": original_config["n_layers"],
        "intermediate_size": original_config["hidden_dim"],
        "num_attention_heads": original_config["n_heads"],
        "num_key_value_heads": original_config["n_kv_heads"],
        "rms_norm_eps": original_config["norm_eps"],
        "vocab_size": original_config["vocab_size"],
        "tie_word_embeddings": original_config.get("tied_embeddings", False),
        "sliding_window": int(original_config["sliding_window"])
        if original_config.get("sliding_window") is not None
        else None,
        "max_position_embeddings": original_config.get(
            "max_position_embeddings", original_config.get("max_seq_len", max_position_embeddings)
        ),
        "bos_token_id": 1,
        "eos_token_id": 2,
        "pad_token_id": 11,
    }

    for key in ["q_lora_rank", "qk_rope_head_dim", "qk_nope_head_dim", "kv_lora_rank", "v_head_dim"]:
        if key in original_config:
            text_kwargs[key] = original_config[key]

    moe = original_config.get("moe")
    assert moe is not None
    text_kwargs.update(
        {
            "n_routed_experts": moe.get("num_experts", 128),
            "num_experts_per_tok": moe.get("num_experts_per_tok", 4),
            "first_k_dense_replace": moe.get("first_k_dense_replace", 0),
            "n_shared_experts": moe.get("num_shared_experts", 1),
            "moe_intermediate_size": moe.get("expert_hidden_dim", 2048),
            "routed_scaling_factor": moe.get("routed_scale", 1.0),
            "n_group": moe.get("num_expert_groups", 1),
            "topk_group": moe.get("num_expert_groups_per_tok", 1),
            "norm_topk_prob": True,
        }
    )

    qk_rope_head_dim = text_kwargs.get("qk_rope_head_dim", 64)
    qk_nope_head_dim = text_kwargs.get("qk_nope_head_dim", 64)

    text_kwargs["rope_parameters"] = {
        "type": "yarn",
        "rope_theta": original_config.get("rope_theta", 10_000.0),
        "factor": float(original_config["yarn"]["factor"]),
        "original_max_position_embeddings": original_config["yarn"]["original_max_position_embeddings"],
        "beta_fast": float(original_config["yarn"]["beta"]),
        "beta_slow": float(original_config["yarn"]["alpha"]),
        "mscale_all_dim": 1.0,
        "mscale": 1.0,
        "llama_4_scaling_beta": original_config.get("llama_4_scaling", {}).get("beta", 0.1),
        "partial_rotary_factor": qk_rope_head_dim / (qk_nope_head_dim + qk_rope_head_dim),
    }

    quant_kwargs: dict[str, Any] = {}
    quant = original_config.get("quantization", {})
    if output_fp8 and quant.get("qformat_weight") == "fp8_e4m3":
        assert quant["qscheme_act"] == "TENSOR"
        quant_kwargs["quantization_config"] = AutoQuantizationConfig.from_dict(
            {
                "activation_scheme": "static",
                "modules_to_not_convert": ["model.vision_tower", "model.multi_modal_projector", "lm_head"],
                "quant_method": "fp8",
                "weight_block_size": None,
            }
        )

    if not is_vision:
        return Mistral4Config(**text_kwargs, **quant_kwargs)

    text_config = Mistral4Config(**text_kwargs)
    adapter_bias = original_vision_config.pop("adapter_bias", False)
    spatial_merge_size = original_vision_config.pop("spatial_merge_size")
    image_token_id = original_vision_config.pop("image_token_id", 10)
    for drop_key in [
        "mm_projector_id",
        "add_pre_mm_projector_layer_norm",
        "image_break_token_id",
        "image_end_token_id",
        "max_image_size",
    ]:
        original_vision_config.pop(drop_key, None)
    vision_config = PixtralVisionConfig(hidden_act="silu", **original_vision_config)

    return Mistral3Config(
        vision_config=vision_config,
        text_config=text_config,
        multimodal_projector_bias=adapter_bias,
        image_token_id=image_token_id,
        spatial_merge_size=spatial_merge_size,
        vision_feature_layer=-1,
        tie_word_embeddings=text_kwargs["tie_word_embeddings"],
        **quant_kwargs,
    )