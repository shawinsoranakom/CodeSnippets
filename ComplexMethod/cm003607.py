def convert_model(
    repo_id=None,
    local_dir=None,
    text_model_id=None,
    output_dir=None,
    output_hub_path=None,
    revision=None,
):
    """Convert and save the model weights, processor, and configuration."""
    if output_dir is None and output_hub_path is None:
        raise ValueError("At least one of output_dir or output_hub_path must be specified")

    if repo_id is None and local_dir is None:
        raise ValueError("Either repo_id or local_dir must be specified")

    # Create output directory if specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        print(f"Created/verified output directory: {output_dir}")

    torch.set_default_dtype(torch.float16)

    # Download or locate model files
    input_path = ensure_model_downloaded(repo_id=repo_id, revision=revision, local_dir=local_dir)

    # Load configuration files
    required_files = ["config.json", "preprocessor_config.json", "special_tokens_map.json", "tokenizer_config.json"]

    missing_files = [f for f in required_files if not os.path.exists(os.path.join(input_path, f))]
    if missing_files:
        raise ValueError(
            f"The following required configuration files are missing from {input_path}: {', '.join(missing_files)}. "
            "Please ensure you have downloaded all necessary model files."
        )

    with open(os.path.join(input_path, "config.json"), "r") as f:
        config_data = json.load(f)
    with open(os.path.join(input_path, "preprocessor_config.json"), "r") as f:
        preprocessor_config = json.load(f)
    with open(os.path.join(input_path, "special_tokens_map.json"), "r") as f:
        special_tokens_map = json.load(f)
    with open(os.path.join(input_path, "tokenizer_config.json"), "r") as f:
        tokenizer_config = json.load(f)

    # Create tokenizer directly from tokenizer.json if it exists
    tokenizer_json_path = os.path.join(input_path, "tokenizer.json")
    special_image_tokens = {
        "image_token": "<image_placeholder>",
        "boi_token": "<begin_of_image>",
        "eoi_token": "<end_of_image>",
    }

    if os.path.exists(tokenizer_json_path) and not text_model_id:
        tokenizer = AutoTokenizer.from_pretrained(
            input_path,  # This will load tokenizer.json directly
            model_max_length=tokenizer_config["model_max_length"],
            extra_special_tokens=special_image_tokens,
        )
    else:
        # Fallback to creating from text_model_id with special tokens
        tokenizer = AutoTokenizer.from_pretrained(
            text_model_id,
            bos_token=special_tokens_map["bos_token"],
            eos_token=special_tokens_map["eos_token"],
            pad_token=special_tokens_map["pad_token"],
            additional_special_tokens=special_tokens_map["additional_special_tokens"],
            model_max_length=tokenizer_config["model_max_length"],
            extra_special_tokens=special_image_tokens,
        )

    # Create image processor from config
    image_processor_kwargs = {}
    for key in ["do_normalize", "image_mean", "image_std", "min_size", "rescale_factor"]:
        if key in preprocessor_config:
            image_processor_kwargs[key] = preprocessor_config[key]

    if "image_size" in preprocessor_config:
        image_processor_kwargs["size"] = {
            "height": preprocessor_config["image_size"],
            "width": preprocessor_config["image_size"],
        }

    image_processor = JanusImageProcessor(**image_processor_kwargs)

    # Create processor with chat template
    processor = JanusProcessor(
        image_processor=image_processor,
        tokenizer=tokenizer,
        chat_template=CHAT_TEMPLATE,
        use_default_system_prompt=True,
    )

    if output_dir:
        print(f"Saving processor to {output_dir}...")
        processor.save_pretrained(output_dir)
    if output_hub_path:
        print(f"Pushing processor to hub at {output_hub_path}...")
        processor.push_to_hub(output_hub_path)

    # Create model configurations
    text_config_kwargs = {}
    for key in [
        "vocab_size",
        "hidden_size",
        "intermediate_size",
        "num_hidden_layers",
        "num_attention_heads",
        "num_key_value_heads",
        "hidden_act",
        "max_position_embeddings",
        "dtype",
    ]:
        if key in config_data["language_config"]:
            text_config_kwargs[key] = config_data["language_config"][key]

    # Add token IDs from tokenizer
    text_config_kwargs.update(
        {
            "pad_token_id": tokenizer.pad_token_id,
            "bos_token_id": tokenizer.bos_token_id,
            "eos_token_id": tokenizer.eos_token_id,
        }
    )

    text_config = LlamaConfig(**text_config_kwargs)

    # Create vision config
    vision_config_kwargs = {}
    if "image_size" in config_data["vision_config"]["params"]:
        vision_config_kwargs["image_size"] = config_data["vision_config"]["params"]["image_size"]

    # Add aligner params if present
    if "aligner_config" in config_data and "params" in config_data["aligner_config"]:
        if "n_embed" in config_data["aligner_config"]["params"]:
            vision_config_kwargs["projection_dim"] = config_data["aligner_config"]["params"]["n_embed"]
        if "depth" in config_data["aligner_config"]["params"]:
            vision_config_kwargs["depth"] = config_data["aligner_config"]["params"]["depth"]

    vision_config = JanusVisionConfig(**vision_config_kwargs)

    vq_config = JanusVQVAEConfig(
        embed_dim=config_data["gen_vision_config"]["params"]["n_embed"],
        num_embeddings=config_data["gen_vision_config"]["params"]["image_token_size"],
        projection_dim=config_data["gen_aligner_config"]["params"]["n_embed"],
        depth=config_data["gen_aligner_config"]["params"]["depth"],
        image_token_embed_dim=config_data["gen_head_config"]["params"]["image_token_embed"],
    )

    # Create the main config
    config = JanusConfig(
        text_config=text_config,
        vision_config=vision_config,
        vq_config=vq_config,
        image_token_id=tokenizer.vocab.get("<image_placeholder>"),
    )

    # Save the config
    if output_dir:
        config.save_pretrained(output_dir)
    if output_hub_path:
        config.push_to_hub(output_hub_path)

    # Initialize model with empty weights
    print("Creating empty model...")
    with torch.device("meta"):
        model = JanusForConditionalGeneration(config)

    model.generation_config._from_model_config = False
    model.generation_config.temperature = 1
    model.generation_config.guidance_scale = 5
    model.generation_config.pad_token_id = tokenizer.vocab.get("<\uff5c\u2581pad\u2581\uff5c>")
    if not hasattr(model.generation_config, "generation_kwargs"):
        model.generation_config.generation_kwargs = {}
    model.generation_config.generation_kwargs["boi_token_id"] = tokenizer.vocab.get("<begin_of_image>")

    # Load and convert state dict
    print("Loading state dict...")
    state_dict = load_model_state_dict(input_path)
    state_dict = convert_state_dict_to_hf(state_dict)

    # Load converted state dict
    print("Loading converted weights into model...")
    model.load_state_dict(state_dict, strict=True, assign=True)

    # Tie weights before any device mapping
    print("Tying weights...")
    model.tie_weights()

    # Save the model
    if output_dir:
        print(f"Saving model to {output_dir}...")
        model.save_pretrained(output_dir)
    if output_hub_path:
        print(f"Pushing model to hub at {output_hub_path}...")
        model.push_to_hub(output_hub_path)

    del state_dict, model
    gc.collect()

    # Validate the saved model if saved locally
    if output_dir:
        print("Reloading the local model to check if it's saved correctly...")
        # TODO: warning about weights not being tied is raised here regardless of model.tie_weights() above
        JanusForConditionalGeneration.from_pretrained(output_dir, device_map="auto")
        print("Local model reloaded successfully.")