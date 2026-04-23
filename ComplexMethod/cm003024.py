def convert_mistral_model(input_dir, output_dir):
    vision_config = {}
    if os.path.isfile(f"{input_dir}/params.json"):
        with open(f"{input_dir}/params.json") as f:
            param_json = json.load(f)
        vision_config = param_json.pop("vision_encoder")
        for k, v in MISTRAL_CONFIG_MAPPING.items():
            value = param_json.pop(k)
            param_json[v] = value
        if "hidden_act" not in vision_config:
            vision_config["hidden_act"] = "silu"
        text_config = MistralConfig(
            **param_json,
            hidden_act="silu",
            sliding_window=None,
            tie_word_embeddings=False,
            rms_norm_eps=1e-5,
        )
    else:
        text_config = MistralConfig(
            attention_dropout=0.0,
            bos_token_id=1,
            eos_token_id=2,
            head_dim=128,
            hidden_act="silu",
            hidden_size=5120,
            initializer_range=0.02,
            intermediate_size=14336,
            max_position_embeddings=1024000,
            model_type="mistral",
            num_attention_heads=32,
            num_hidden_layers=40,
            num_key_value_heads=8,
            rms_norm_eps=1e-05,
            rope_theta=1000000000.0,
            sliding_window=None,
            tie_word_embeddings=False,
            vocab_size=131072,
        )
    adapter_bias = vision_config.pop("adapter_bias", True)
    vision_config = PixtralVisionConfig(**vision_config)
    config = LlavaConfig(
        vision_config,
        text_config,
        vision_feature_layer=-1,
        image_token_id=10,
        vision_feature_select_strategy="full",
        image_seq_length=1,
        multimodal_projector_bias=adapter_bias,
    )
    config.architectures = ["LlavaForConditionalGeneration"]
    config.save_pretrained(output_dir)
    full_original_state_dict = {}
    safetensors_files = sorted([file for file in os.listdir(input_dir) if file.endswith(".safetensors")])
    if len(safetensors_files) == 1:
        full_original_state_dict = safe_load_file(f"{input_dir}/consolidated.safetensors")
    else:
        for file in safetensors_files:
            loaded_dict = safe_load_file(f"{input_dir}/{file}")
            full_original_state_dict.update(loaded_dict)

    new_dict = convert_dictionary(full_original_state_dict, vision_config, text_config)
    with torch.device("meta"):
        model = LlavaForConditionalGeneration(config)
    model.load_state_dict(new_dict, strict=True, assign=True)
    model.save_pretrained(output_dir)