def convert_and_write_model(input_dir: str, output_dir: str, max_position_embeddings: int):
    """Convert the model and save it (this implicitly save the config as well)."""
    params = read_json(os.path.join(input_dir, "params.json"))

    is_vision = params.get("vision_encoder") is not None
    config = convert_config(params, max_position_embeddings, is_vision)

    full_state_dict = {}
    # The model may be split between different files, but a single nn.Module is always fully present in a single file
    shards = [file for file in os.listdir(input_dir) if file.endswith(".safetensors")]
    for shard_file in shards:
        original_state_dict = load_file(os.path.join(input_dir, shard_file))
        new_dict = convert_state_dict(original_state_dict, config)
        full_state_dict.update(new_dict)

    text_config = config.text_config if is_vision else config
    if text_config.tie_word_embeddings:
        model_key = "model.language_model" if is_vision else "model"
        full_state_dict["lm_head.weight"] = full_state_dict[f"{model_key}.embed_tokens.weight"]

    # Load weights into model and resave them
    with torch.device("meta"):
        if isinstance(config, Mistral3Config):
            model = Mistral3ForConditionalGeneration(config)
        elif isinstance(config, Ministral3Config):
            model = Ministral3ForCausalLM(config)
        else:
            raise ValueError(f"Unknown config type {type(config)}.")

        # let's swap nn.Linear to FP8 Linear before loading
        if hasattr(model.config, "quantization_config"):
            model = replace_with_fp8_linear(
                model, model.config.quantization_config.modules_to_not_convert, model.config.quantization_config
            )

    model.load_state_dict(full_state_dict, strict=True, assign=True)
    model.save_pretrained(output_dir)
    return config