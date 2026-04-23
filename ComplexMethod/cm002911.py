def convert_sam3_checkpoint(
    checkpoint_path: str,
    output_path: str,
    config: Sam3Config | None = None,
    push_to_hub: bool = False,
    repo_id: str | None = None,
):
    """
    Convert SAM3 checkpoint from original format to HuggingFace format.

    Args:
        checkpoint_path: Path to the original checkpoint file
        output_path: Path to save the converted checkpoint
        config: Optional Sam3Config to use (otherwise creates default)
        push_to_hub: Whether to push the model to the Hub
        repo_id: Repository ID for pushing to Hub
    """
    # Create output directory
    os.makedirs(output_path, exist_ok=True)

    # Load configuration
    if config is None:
        config = get_sam3_config()

    config.architectures = ["Sam3Model"]
    config.save_pretrained(output_path)
    print("Model config saved successfully")

    # Load and convert weights
    print("Loading original checkpoint...")
    state_dict_old = load_original_state_dict(checkpoint_path)

    print("Converting checkpoint keys...")
    all_keys = list(state_dict_old.keys())
    key_mapping = convert_old_keys_to_new_keys(all_keys)

    # Create new state dict with converted keys
    state_dict_new = {}

    for old_key in all_keys:
        new_key = key_mapping.get(old_key, old_key)
        # Special handling: Strip cls token from vision backbone position embeddings
        if new_key == "vision_encoder.backbone.embeddings.position_embeddings":
            # Original has [1, 577, 1024] with cls token, but refactored expects [1, 576, 1024] without cls token
            # Strip the first position (cls token position)
            state_dict_new[new_key] = state_dict_old[old_key][:, 1:, :]
        else:
            state_dict_new[new_key] = state_dict_old[old_key]

    del state_dict_old
    gc.collect()

    # Split combined QKV projections into separate Q, K, V projections
    print("Splitting QKV projections...")
    state_dict_new = split_qkv(state_dict_new)

    # Transpose CLIP text projection (stored transposed in original)
    if "text_encoder.text_projection.weight" in state_dict_new:
        print("Transposing CLIP text_projection...")
        state_dict_new["text_encoder.text_projection.weight"] = state_dict_new["text_encoder.text_projection.weight"].T

    # Load into HF model
    print("Loading weights into Sam3Model...")
    model = Sam3Model(config)
    missing_keys, unexpected_keys = model.load_state_dict(state_dict_new, strict=False)

    if missing_keys:
        logger.warning(f"Missing keys ({len(missing_keys)}):")
        for key in missing_keys:  # Show more keys for debugging
            logger.warning(f"  - {key}")

    if unexpected_keys:
        logger.warning(f"Unexpected keys ({len(unexpected_keys)}):")
        for key in unexpected_keys:  # Show more keys for debugging
            logger.warning(f"  - {key}")

    # Note: Some missing/unexpected keys are expected:
    # - vision_encoder.backbone.embeddings.patch_embeddings.projection.bias: patch projection has bias=False
    # - geometry_encoder.mask_encoder.projection.*: this is nn.Identity() in original (no weights)
    # - rotary_emb.rope_embeddings: pre-computed in original, computed on-the-fly in refactored
    # - text_encoder.text_projection.bias: projection layer might not have bias

    # Save model
    print(f"Saving converted model to {output_path}")
    model.save_pretrained(
        output_path,
    )

    # Save processor
    print("Creating and saving processor...")
    image_processor = Sam3ImageProcessor()
    tokenizer = CLIPTokenizerFast.from_pretrained("openai/clip-vit-base-patch32", max_length=32, model_max_length=32)
    processor = Sam3Processor(image_processor=image_processor, tokenizer=tokenizer)
    processor.save_pretrained(output_path)

    # Push to hub if requested
    if push_to_hub:
        if repo_id is None:
            raise ValueError("repo_id must be provided when push_to_hub=True")
        print(f"Pushing model to Hub: {repo_id}")
        model.push_to_hub(repo_id)
        processor.push_to_hub(repo_id)

    print("Conversion complete!")
    print(f"Model saved successfully to: {output_path}")

    # Cleanup
    del state_dict_new, model
    gc.collect()

    # Verify the conversion by reloading
    print("\nVerifying converted checkpoint can be loaded...")
    try:
        model = Sam3Model.from_pretrained(output_path)
        param_count = sum(p.numel() for p in model.parameters())
        print(f"✓ Successfully loaded model with {param_count:,} parameters")
        del model
        gc.collect()
    except Exception as e:
        print(f"✗ Failed to reload model: {e}")

    print("\n" + "=" * 80)
    print("Conversion finished!")
    print("=" * 80)
    print(f"Output directory: {output_path}")
    print("\nTo test the model, you can run:")
    print(">>> from transformers import Sam3Model")
    print(f">>> model = Sam3Model.from_pretrained('{output_path}')")
    print("=" * 80)