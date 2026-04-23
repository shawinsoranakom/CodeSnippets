def get_internvl_config(input_base_path):
    base_config = AutoModel.from_pretrained(input_base_path, trust_remote_code=True).config
    llm_config = base_config.llm_config.to_dict()
    vision_config = base_config.vision_config.to_dict()
    vision_config["use_absolute_position_embeddings"] = True
    if get_lm_type(input_base_path) == "qwen2":
        image_token_id = 151667
        language_config_class = Qwen2Config
    else:
        image_token_id = 92546
        language_config_class = LlamaConfig

    llm_config = {k: v for k, v in llm_config.items() if k not in UNNECESSARY_CONFIG_KEYS}
    # Force use_cache to True
    llm_config["use_cache"] = True
    # Force correct eos_token_id for InternVL3
    if "InternVL3" in input_base_path and get_lm_type(input_base_path) == "qwen2":
        llm_config["eos_token_id"] = 151645

    vision_config = {k: v for k, v in vision_config.items() if k not in UNNECESSARY_CONFIG_KEYS}
    if "attention_probs_dropout_prob" in vision_config:
        attention_dropout = vision_config.pop("attention_probs_dropout_prob")
        vision_config["attention_dropout"] = attention_dropout
        vision_config["projection_dropout"] = attention_dropout
    if "qk_normalization" in vision_config:
        use_qk_norm = vision_config.pop("qk_normalization")
        vision_config["use_qk_norm"] = use_qk_norm
    if "qkv_bias" in vision_config:
        attention_bias = vision_config.pop("qkv_bias")
        vision_config["attention_bias"] = attention_bias

    return InternVLConfig(
        text_config=language_config_class(**llm_config),
        vision_config=InternVLVisionConfig(**vision_config),
        image_token_id=image_token_id,
    )