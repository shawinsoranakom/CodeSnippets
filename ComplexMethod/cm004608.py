def convert_model(
    hf_repo_id: str,
    output_dir: str | None = None,
    output_hub_path: str | None = None,
):
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        input_path = snapshot_download(hf_repo_id)
    except HFValidationError:
        # If the input path is not a HF repo ID, assume it's a local path
        input_path = hf_repo_id

    # ------------------------------------------------------------
    # Create and save config
    # ------------------------------------------------------------

    config = DeepseekVLConfig(
        text_config={
            "hidden_size": 2048,
            "intermediate_size": 5632,
            "max_position_embeddings": 16384,
            "num_attention_heads": 16,
            "num_hidden_layers": 24,
            "vocab_size": 102400,
        },
        vision_config={
            "hidden_size": 1024,
            "intermediate_size": 4096,
            "image_size": 384,
            "patch_size": 16,
            "hidden_act": "gelu",
            "vision_use_head": False,
            "num_attention_heads": 16,
            "num_hidden_layers": 24,
        },
    )

    # save config
    if output_dir:
        config.save_pretrained(output_dir)
        print("Model config saved successfully...")

    # ------------------------------------------------------------
    # Convert processor
    # ------------------------------------------------------------

    image_processor = DeepseekVLImageProcessor(
        image_mean=IMAGENET_STANDARD_MEAN,
        image_std=IMAGENET_STANDARD_STD,
    )

    tokenizer = AutoTokenizer.from_pretrained(
        input_path,
        extra_special_tokens={
            "pad_token": "<｜end▁of▁sentence｜>",
            "image_token": "<image_placeholder>",
        },
    )

    processor = DeepseekVLProcessor(
        image_processor=image_processor,
        tokenizer=tokenizer,
        chat_template=CHAT_TEMPLATE,
    )

    if output_dir:
        print(f"Saving processor to {output_dir}...")
        processor.save_pretrained(output_dir)
    if output_hub_path:
        print(f"Pushing processor to hub at {output_hub_path}...")
        processor.push_to_hub(output_hub_path)

    # ------------------------------------------------------------
    # Convert weights
    # ------------------------------------------------------------

    print("Creating empty model...")
    with torch.device("meta"):
        model = DeepseekVLForConditionalGeneration(config)

    # Load and convert state dict
    print("Loading state dict...")
    state_dict = load_model_state_dict(input_path)
    state_dict = update_state_dict(state_dict)

    # Load converted state dict
    print("Loading converted weights into model...")
    info = model.load_state_dict(state_dict, strict=False, assign=True)
    if len(info.missing_keys) > 0:
        raise ValueError(f"Missing keys: {info.missing_keys}")

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
        DeepseekVLForConditionalGeneration.from_pretrained(output_dir, device_map="auto")
        print("Local model reloaded successfully.")