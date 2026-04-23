def convert_lw_detr_checkpoint(
    model_name: str,
    checkpoint_path: str,
    pytorch_dump_folder_path: str,
    push_to_hub: bool = False,
    organization: str = "huggingface",
):
    """
    Convert a LW-DETR checkpoint to HuggingFace format.

    Args:
        model_name: Name of the model (e.g., "lwdetr_tiny_30e_objects365")
        checkpoint_path: Path to the checkpoint file
        pytorch_dump_folder_path: Path to save the converted model
        push_to_hub: Whether to push the model to the hub
        organization: Organization to push the model to
    """
    print(f"Converting {model_name} checkpoint...")

    # Create output directory
    os.makedirs(pytorch_dump_folder_path, exist_ok=True)

    # Get model configuration
    config = get_model_config(model_name)
    lw_detr_config = LwDetrConfig(**config)

    # Save configuration
    lw_detr_config.save_pretrained(pytorch_dump_folder_path)
    print("Configuration saved successfully...")

    # Load checkpoint
    print(f"Loading checkpoint from {checkpoint_path}...")
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)

    # Create model and load weights
    print("Creating model and loading weights...")
    model = LwDetrForObjectDetection(lw_detr_config)

    # Handle different checkpoint formats
    if "state_dict" in checkpoint:
        state_dict = checkpoint["state_dict"]
    elif "model" in checkpoint:
        state_dict = checkpoint["model"]
    else:
        state_dict = checkpoint

    # Convert keys if needed
    if ORIGINAL_TO_CONVERTED_KEY_MAPPING:
        backbone_projector_sampling_key_mapping = get_backbone_projector_sampling_key_mapping(lw_detr_config)
        state_dict = backbone_read_in_q_k_v(state_dict, lw_detr_config)
        state_dict = read_in_q_k_v(state_dict, lw_detr_config)
        key_mapping = ORIGINAL_TO_CONVERTED_KEY_MAPPING | backbone_projector_sampling_key_mapping
        all_keys = list(state_dict.keys())
        new_keys = convert_old_keys_to_new_keys(all_keys, key_mapping)
        prefix = "model."
        converted_state_dict = {}
        for key in all_keys:
            if not any(key.startswith(prefix) for prefix in ["class_embed", "bbox_embed"]):
                new_key = new_keys[key]
                converted_state_dict[prefix + new_key] = state_dict[key]
            else:
                converted_state_dict[key] = state_dict[key]

    # Load state dict
    missing_keys, unexpected_keys = model.load_state_dict(converted_state_dict, strict=False)
    if missing_keys:
        print(f"Missing keys: {missing_keys}")
    if unexpected_keys:
        print(f"Unexpected keys: {unexpected_keys}")

    # Save model
    print("Saving model...")
    model.save_pretrained(pytorch_dump_folder_path)

    # Save image processor
    print("Saving image processor...")
    image_processor = DeformableDetrImageProcessor(size={"height": 640, "width": 640})
    image_processor.save_pretrained(pytorch_dump_folder_path)

    test_models_outputs(model, image_processor, model_name)

    if push_to_hub:
        print("Pushing model to hub...")
        model.push_to_hub(repo_id=f"{organization}/{model_name}", commit_message=f"Add {model_name} model")
        lw_detr_config.push_to_hub(repo_id=f"{organization}/{model_name}", commit_message=f"Add {model_name} config")
        image_processor.push_to_hub(
            repo_id=f"{organization}/{model_name}", commit_message=f"Add {model_name} image processor"
        )
        print("Pushed model to hub successfully!")

    print(f"Conversion completed successfully for {model_name}!")