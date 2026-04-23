def create_config_from_checkpoint(checkpoint_path: str | Path) -> VibeVoiceAsrConfig:
    checkpoint_path = Path(checkpoint_path)
    config_path = (
        checkpoint_path / "config.json" if checkpoint_path.is_dir() else checkpoint_path.parent / "config.json"
    )

    if config_path.exists():
        with open(config_path, "r") as f:
            original_config = json.load(f)

        config_keys_to_remove = [
            "decoder_depths",
            "decoder_n_filters",
            "decoder_ratios",
            "std_dist_type",
            "fix_std",
            "pad_mode",
            "conv_bias",
            "causal",
            "mixer_layer",
            "layernorm",
            "disable_last_norm",
            "conv_norm",
            "corpus_normalize",
            "layernorm_elementwise_affine",
        ]

        # Prepare acoustic tokenizer config
        acoustic_config_dict = original_config.get("acoustic_tokenizer_config", {}).copy()
        if "encoder_depths" in acoustic_config_dict and isinstance(acoustic_config_dict["encoder_depths"], str):
            acoustic_config_dict["encoder_depths"] = list(map(int, acoustic_config_dict["encoder_depths"].split("-")))
        if "layernorm_eps" in acoustic_config_dict:
            acoustic_config_dict["rms_norm_eps"] = acoustic_config_dict.pop("layernorm_eps")
        if "encoder_ratios" in acoustic_config_dict:
            acoustic_config_dict["downsampling_ratios"] = list(reversed(acoustic_config_dict.pop("encoder_ratios")))
        if "encoder_n_filters" in acoustic_config_dict:
            acoustic_config_dict["num_filters"] = acoustic_config_dict.pop("encoder_n_filters")
        if "encoder_depths" in acoustic_config_dict:
            acoustic_config_dict["depths"] = acoustic_config_dict.pop("encoder_depths")
        if "vae_dim" in acoustic_config_dict:
            acoustic_config_dict["hidden_size"] = acoustic_config_dict.pop("vae_dim")
        if "fix_std" in acoustic_config_dict:
            acoustic_config_dict["vae_std"] = acoustic_config_dict.pop("fix_std") / 0.8
        for key in config_keys_to_remove:
            acoustic_config_dict.pop(key, None)
        acoustic_tokenizer_encoder_config = VibeVoiceAcousticTokenizerEncoderConfig(**acoustic_config_dict)

        # Prepare semantic tokenizer config
        semantic_config_dict = original_config.get("semantic_tokenizer_config", {}).copy()
        if "encoder_depths" in semantic_config_dict and isinstance(semantic_config_dict["encoder_depths"], str):
            semantic_config_dict["encoder_depths"] = list(map(int, semantic_config_dict["encoder_depths"].split("-")))
        if "layernorm_eps" in semantic_config_dict:
            semantic_config_dict["rms_norm_eps"] = semantic_config_dict.pop("layernorm_eps")
        if "encoder_ratios" in semantic_config_dict:
            semantic_config_dict["downsampling_ratios"] = list(reversed(semantic_config_dict.pop("encoder_ratios")))
        if "encoder_n_filters" in semantic_config_dict:
            semantic_config_dict["num_filters"] = semantic_config_dict.pop("encoder_n_filters")
        if "encoder_depths" in semantic_config_dict:
            semantic_config_dict["depths"] = semantic_config_dict.pop("encoder_depths")
        if "vae_dim" in semantic_config_dict:
            semantic_config_dict["hidden_size"] = semantic_config_dict.pop("vae_dim")
        for key in config_keys_to_remove:
            semantic_config_dict.pop(key, None)
        semantic_tokenizer_encoder_config = VibeVoiceAcousticTokenizerEncoderConfig(**semantic_config_dict)

        # Create main config
        config = VibeVoiceAsrConfig(
            acoustic_tokenizer_encoder_config=acoustic_tokenizer_encoder_config,
            semantic_tokenizer_encoder_config=semantic_tokenizer_encoder_config,
            text_config=Qwen2Config(**original_config.get("decoder_config", {})),
        )
    else:
        logger.warning("No config.json found, using default configuration")
        config = VibeVoiceAsrConfig()

    return config