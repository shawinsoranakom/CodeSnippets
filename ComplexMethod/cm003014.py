def convert_config(original_config: dict, max_position_embeddings: int = 262144, is_vision: bool = True):
    original_vision_config = original_config.pop("vision_encoder", None)
    assert is_vision == (original_vision_config is not None), (
        f"is_vision={is_vision} but original_vision_config={original_vision_config}"
    )
    original_text_config = original_config

    # Text config
    text_key_mapping = {
        "hidden_size": "dim",
        "num_hidden_layers": "n_layers",
        "intermediate_size": "hidden_dim",
        "num_attention_heads": "n_heads",
        "num_key_value_heads": "n_kv_heads",
        "rms_norm_eps": "norm_eps",
    }
    similar_text_keys_to_keep = [
        "head_dim",
        "vocab_size",
    ]

    new_text_config_kwargs = {k: original_text_config[v] for k, v in text_key_mapping.items()}
    new_text_config_kwargs.update({k: v for k, v in original_text_config.items() if k in similar_text_keys_to_keep})
    tie_word_embeddings = original_text_config.get("tied_embeddings", False)
    new_text_config_kwargs["tie_word_embeddings"] = tie_word_embeddings
    new_text_config_kwargs["rope_parameters"] = {
        "type": "yarn",
        "rope_theta": original_config.get("rope_theta", 1000000.0),
        "factor": float(original_config["yarn"]["factor"]),
        "original_max_position_embeddings": original_config["yarn"]["original_max_position_embeddings"],
        "beta_fast": float(original_config["yarn"]["beta"]),
        "beta_slow": float(original_config["yarn"]["alpha"]),
        "mscale_all_dim": 1.0 if is_vision else 0.0,
        "mscale": 1.0,
        "llama_4_scaling_beta": original_config.get("llama_4_scaling", {}).get("beta", 0),
    }

    # These are not always defined depending on `params.json`
    new_text_config_kwargs["sliding_window"] = original_text_config.get("sliding_window", None)
    new_text_config_kwargs["max_position_embeddings"] = original_text_config.get(
        "max_position_embeddings", original_text_config.get("max_seq_len", max_position_embeddings)
    )
    # This may sometimes be a string in `params.json`
    if new_text_config_kwargs["sliding_window"] is not None:
        new_text_config_kwargs["sliding_window"] = int(new_text_config_kwargs["sliding_window"])

    def get_maybe_quant_config() -> dict:
        kwargs = {}
        if original_config.get("quantization", {}).get("qformat_weight") == "fp8_e4m3":
            assert original_config["quantization"]["qscheme_act"] == "TENSOR"
            quantization_config = {
                "activation_scheme": "static",
                "modules_to_not_convert": ["model.vision_tower", "model.multi_modal_projector", "lm_head"],
                "quant_method": "fp8",
                "weight_block_size": None,
            }
            kwargs["quantization_config"] = AutoQuantizationConfig.from_dict(quantization_config)
        return kwargs

    # No vision
    if original_vision_config is None:
        new_text_config = Ministral3Config(**new_text_config_kwargs, **get_maybe_quant_config())
        return new_text_config
    else:
        new_text_config = Ministral3Config(**new_text_config_kwargs)

    # Vision config
    new_vision_config = original_vision_config
    adapter_bias = new_vision_config.pop("adapter_bias", False)
    _ = new_vision_config.pop("mm_projector_id", None)
    _ = new_vision_config.pop("add_pre_mm_projector_layer_norm", None)
    spatial_merge_size = new_vision_config.pop("spatial_merge_size")
    image_token_id = new_vision_config.pop("image_token_id", 10)
    _ = new_vision_config.pop("image_break_token_id", 12)
    _ = new_vision_config.pop("image_end_token_id", 13)
    _ = new_vision_config.pop("max_image_size")
    new_vision_config = PixtralVisionConfig(hidden_act="silu", **new_vision_config)

    new_config = Mistral3Config(
        vision_config=new_vision_config,
        text_config=new_text_config,
        multimodal_projector_bias=adapter_bias,
        image_token_id=image_token_id,
        spatial_merge_size=spatial_merge_size,
        vision_feature_layer=-1,
        **get_maybe_quant_config(),
    )
    return new_config