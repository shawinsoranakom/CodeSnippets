def convert_sam3_lite_text_checkpoint(
    checkpoint_path: str,
    output_path: str,
    config: Sam3LiteTextConfig | None = None,
    push_to_hub: bool = False,
    repo_id: str | None = None,
):
    """
    Convert an EfficientSAM3 LiteText checkpoint to HuggingFace format.

    Args:
        checkpoint_path: Path to the original `.pt` checkpoint file.
        output_path: Directory where the converted model will be saved.
        config: Optional pre-built `Sam3LiteTextConfig` (defaults to auto-inferred).
        push_to_hub: Whether to push the model to the Hugging Face Hub.
        repo_id: Hub repository ID (required when ``push_to_hub=True``).
    """
    os.makedirs(output_path, exist_ok=True)

    # Load original checkpoint
    state_dict_old = load_original_state_dict(checkpoint_path)

    # Build config from checkpoint
    if config is None:
        config = get_sam3_lite_text_config(state_dict_old)

    config.architectures = ["Sam3LiteTextModel"]
    config.save_pretrained(output_path)
    print("Model config saved successfully")

    # Convert keys
    print("Converting checkpoint keys...")
    all_keys = list(state_dict_old.keys())
    key_mapping = convert_old_keys_to_new_keys(all_keys)

    state_dict_new = {}
    for old_key in all_keys:
        new_key = key_mapping.get(old_key, old_key)
        # num_batches_tracked from BatchNorm is not needed
        if "num_batches_tracked" in new_key:
            continue
        # Parallel SAM2 neck branch in the original checkpoint; HF vision uses `convs` only.
        if "vision_backbone.sam2_convs" in new_key:
            continue
        # Drop keys whose names were not transformed (unrecognised / legacy keys)
        if new_key == old_key:
            continue
        # Strip the first position (cls token) from ViT position embeddings
        if new_key == "vision_encoder.backbone.embeddings.position_embeddings":
            state_dict_new[new_key] = state_dict_old[old_key][:, 1:, :]
        else:
            state_dict_new[new_key] = state_dict_old[old_key]

    del state_dict_old
    gc.collect()

    # Split combined QKV projections
    print("Splitting QKV projections...")
    state_dict_new = split_qkv(state_dict_new)

    # HF models compute the RoPE table on the fly
    for k in list(state_dict_new.keys()):
        if k.endswith("rotary_emb.rope_embeddings"):
            state_dict_new.pop(k)

    print(
        "Converted key counts:",
        {
            prefix: sum(1 for k in state_dict_new if k.startswith(prefix))
            for prefix in (
                "vision_encoder.",
                "text_encoder.",
                "geometry_encoder.",
                "detr_encoder.",
                "detr_decoder.",
                "mask_decoder.",
            )
        },
    )

    # Load weights into HF model
    print("Loading weights into Sam3LiteTextModel...")
    model = Sam3LiteTextModel(config)
    missing_keys, unexpected_keys = model.load_state_dict(state_dict_new, strict=False)

    if missing_keys:
        logger.warning(f"Missing keys ({len(missing_keys)}):")
        for key in missing_keys:
            logger.warning(f"  - {key}")

    if unexpected_keys:
        logger.warning(f"Unexpected keys ({len(unexpected_keys)}):")
        for key in unexpected_keys:
            logger.warning(f"  - {key}")

    # Save model
    print(f"Saving converted model to {output_path}")
    model.save_pretrained(output_path)

    # Save processor
    print("Creating and saving processor...")
    image_processor = Sam3ImageProcessor()
    tokenizer = CLIPTokenizerFast.from_pretrained(
        "openai/clip-vit-base-patch32",
        max_length=config.text_config.max_position_embeddings,
        model_max_length=config.text_config.max_position_embeddings,
    )
    processor = Sam3Processor(image_processor=image_processor, tokenizer=tokenizer)
    processor.save_pretrained(output_path)

    if push_to_hub:
        if repo_id is None:
            raise ValueError("repo_id must be provided when push_to_hub=True")
        print(f"Pushing model to Hub: {repo_id}")
        model.push_to_hub(repo_id)
        processor.push_to_hub(repo_id)

    print("Conversion complete!")

    # Cleanup and verify
    del state_dict_new, model
    gc.collect()

    print("\nVerifying converted checkpoint can be loaded...")
    try:
        model = Sam3LiteTextModel.from_pretrained(output_path)
        param_count = sum(p.numel() for p in model.parameters())
        print(f"Successfully loaded model with {param_count:,} parameters")
        del model
        gc.collect()
    except Exception as e:
        print(f"Failed to reload model: {e}")

    print("\n" + "=" * 80)
    print("Conversion finished!")
    print("=" * 80)
    print(f"Output directory: {output_path}")
    print("\nTo use the model:")
    print(">>> from transformers import Sam3LiteTextModel, Sam3Processor")
    print(f">>> model = Sam3LiteTextModel.from_pretrained('{output_path}')")
    print("=" * 80)