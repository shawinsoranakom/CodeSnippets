def convert_chmv2_checkpoint(
    head_checkpoint_path: str,
    pytorch_dump_folder_path: str,
    backbone_checkpoint_path: str | None = None,
    model_name: str = "chmv2",
    backbone_repo_id: str | None = None,
    push_to_hub: bool = False,
    verify_image_path: str | None = None,
) -> None:
    """
    Convert CHMv2 checkpoints to HuggingFace format.

    Accepts head-only or combined (backbone + head) checkpoint. Optionally a separate
    backbone checkpoint or backbone_repo_id for a pre-converted DINOv3.
    """
    os.makedirs(pytorch_dump_folder_path, exist_ok=True)

    config = get_chmv2_config(model_name=model_name, backbone_repo_id=backbone_repo_id)

    # Load checkpoint(s)
    logger.info(f"Loading checkpoint from {head_checkpoint_path}")
    head_ckpt = load_original_state_dict(head_checkpoint_path)

    has_backbone_keys = any(k.startswith("backbone.") for k in head_ckpt.keys())
    head_only = (not has_backbone_keys) and any(k.startswith("reassemble_blocks.") for k in head_ckpt.keys())

    state_dict = {}

    if backbone_checkpoint_path is not None:
        logger.info(f"Loading backbone from {backbone_checkpoint_path}")
        backbone_raw = load_original_state_dict(backbone_checkpoint_path)
        backbone_raw = {f"backbone.{k}": v for k, v in backbone_raw.items()}
        state_dict.update(convert_backbone_keys(backbone_raw))
    elif has_backbone_keys:
        logger.info("Converting backbone keys from checkpoint")
        state_dict.update(convert_backbone_keys(head_ckpt))

    logger.info(f"Converting head weights (head_only={head_only})")
    state_dict.update(convert_head_keys(head_ckpt))

    # Load into model
    model = CHMv2ForDepthEstimation(config)
    missing, unexpected = model.load_state_dict(state_dict, strict=False)

    missing_non_inv = [k for k in missing if "inv_freq" not in k]
    if missing_non_inv:
        logger.warning(f"Missing keys (non-inv_freq): {missing_non_inv}")
    if unexpected:
        logger.warning(f"Unexpected keys: {unexpected}")

    model.eval()

    # Optional verification
    if verify_image_path is not None:
        logger.info(f"Verifying with image: {verify_image_path}")
        image = Image.open(verify_image_path)
        processor = CHMv2ImageProcessor()
        inputs = processor(images=[image], return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
        results = processor.post_process_depth_estimation(outputs, target_sizes=[(image.height, image.width)])
        depth = results[0]["predicted_depth"]
        print(
            f"Predicted depth — shape: {depth.shape}  mean: {depth.mean():.4f}  range: [{depth.min():.4f}, {depth.max():.4f}]"
        )

    # Save
    logger.info(f"Saving to {pytorch_dump_folder_path}")
    model.save_pretrained(pytorch_dump_folder_path)
    processor = CHMv2ImageProcessor()
    processor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        repo_id = f"facebook/{model_name}-hf"
        logger.info(f"Pushing to hub: {repo_id}")
        model.push_to_hub(repo_id=repo_id)
        processor.push_to_hub(repo_id=repo_id)

    print("Conversion complete!")
    print(f"Model saved to: {pytorch_dump_folder_path}")