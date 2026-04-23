def convert_checkpoint(checkpoint, config_path, push_to_hub, bfloat16, processor_config=None):
    if bfloat16:
        dtype = torch.bfloat16
    else:
        dtype = torch.float32

    # 1) Load state dict from safetensors checkpoint
    logger.info(f"Loading checkpoint from {checkpoint}")
    original_state_dict = load_file(checkpoint)

    # 2) Prepare feature extractor
    audio_config = {}
    if processor_config is not None:
        with open(processor_config, "r") as f:
            processor_config = json.load(f)
        audio_config = processor_config.get("audio_processor", {})
    if "sampling_rate" not in audio_config:
        audio_config["sampling_rate"] = 24000
    if "normalize_audio" not in audio_config:
        audio_config["normalize_audio"] = True
    if "target_dB_FS" not in audio_config:
        audio_config["target_dB_FS"] = -25
    if "eps" not in audio_config:
        audio_config["eps"] = 1e-6
    feature_extractor = VibeVoiceAcousticTokenizerFeatureExtractor(**audio_config)

    # 3) Prepare model configuration
    with open(config_path, "r") as f:
        model_config = json.load(f)

    # Clean up acoustic tokenizer config
    acoustic_config_dict = model_config["acoustic_tokenizer_config"].copy()
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
        # Original hardcodes a scaling factor for vae_std
        acoustic_config_dict["vae_std"] = acoustic_config_dict.pop("fix_std") / 0.8

    # Remove unused/constant parameters
    for key in [
        "decoder_depths",
        "decoder_n_filters",
        "decoder_ratios",
        "std_dist_type",
        "pad_mode",
        "conv_bias",
        "causal",
        "mixer_layer",
        "layernorm",
        "disable_last_norm",
        "conv_norm",
        "corpus_normalize",
        "layernorm_elementwise_affine",
    ]:
        acoustic_config_dict.pop(key, None)

    # 4) Convert state dict to match HF model structure
    logger.info("Converting state dict")
    converted_state_dict = convert_state_dict(original_state_dict)

    # 5) Filter for acoustic tokenizer weights
    acoustic_state_dict = {
        k: v for k, v in converted_state_dict.items() if k.startswith("encoder.") or k.startswith("decoder.")
    }

    # 6) Create and save acoustic tokenizer
    logger.info("Creating acoustic tokenizer model")
    acoustic_config = VibeVoiceAcousticTokenizerConfig(**acoustic_config_dict)
    acoustic_model = VibeVoiceAcousticTokenizerModel(acoustic_config).to(dtype)

    # Load weights into HF model
    logger.info("Loading weights into model")
    missing, unexpected = acoustic_model.load_state_dict(acoustic_state_dict, strict=False)
    if len(unexpected) != 0:
        raise ValueError(f"Unexpected keys: {unexpected}")
    if len(missing) != 0:
        raise ValueError(f"Missing keys: {missing}")

    if push_to_hub:
        logger.info(f"Pushing to hub as {push_to_hub}")
        feature_extractor.push_to_hub(push_to_hub)
        acoustic_model.push_to_hub(push_to_hub)

        gc.collect()
        logger.info("Verifying conversion by reloading model")
        AutoFeatureExtractor.from_pretrained(push_to_hub)
        AutoModel.from_pretrained(push_to_hub, dtype=torch.bfloat16, device_map="auto")
        logger.info("Model reloaded successfully!")
        logger.info("Conversion complete!")