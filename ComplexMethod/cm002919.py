def convert_model(
    repo_id=None,
    local_dir=None,
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

    with open(os.path.join(input_path, "config.json"), "r") as f:
        config_data = json.load(f)
    # Pop off unwanted keys
    _ = config_data.pop("backbone", None)

    config = EomtConfig(
        **{
            **config_data,
            "layerscale_value": 1e-5,
        }
    )

    if "semantic" in repo_id.split("_"):
        size = {"shortest_edge": config.image_size, "longest_edge": None}
        do_split_image = True
        do_pad = False
    else:
        size = {"shortest_edge": config.image_size, "longest_edge": config.image_size}
        do_split_image = False
        do_pad = True

    if "giant" in repo_id.split("_"):
        config.use_swiglu_ffn = True
        config.hidden_size = 1536
        config.num_hidden_layers = 40
        config.num_attention_heads = 24
        # Update MAPPINGS for ckpts depending on the MLP type
        MAPPINGS.update(MLP_MAPPINGS["swiglu_ffn"])
    else:
        MAPPINGS.update(MLP_MAPPINGS["vanilla_mlp"])

    processor = EomtImageProcessorFast(size=size, do_split_image=do_split_image, do_pad=do_pad)

    # Save the config and processor
    if output_dir:
        config.save_pretrained(output_dir)
        processor.save_pretrained(output_dir)
    if output_hub_path:
        config.push_to_hub(output_hub_path)
        processor.push_to_hub(output_hub_path)

    # Initialize model with empty weights
    print("Creating empty model...")
    with torch.device("meta"):
        model = EomtForUniversalSegmentation(config)

    # Load and convert state dict
    print("Loading state dict...")
    state_dict = load_model_state_dict(input_path)
    state_dict = convert_state_dict_to_hf(state_dict)

    # Load converted state dict
    print("Loading converted weights into model...")
    model.load_state_dict(state_dict, strict=True, assign=True)

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
        EomtForUniversalSegmentation.from_pretrained(output_dir, device_map="auto")
        print("Local model reloaded successfully.")