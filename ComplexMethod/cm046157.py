def _load_checkpoint(model, checkpoint, interactive=False):
    """Load SAM3 model checkpoint from file."""
    with open(checkpoint, "rb") as f:
        ckpt = torch_load(f)
    if "model" in ckpt and isinstance(ckpt["model"], dict):
        ckpt = ckpt["model"]
    sam3_image_ckpt = {k.replace("detector.", ""): v for k, v in ckpt.items() if "detector" in k}
    if interactive:
        sam3_image_ckpt.update(
            {
                k.replace("backbone.vision_backbone", "image_encoder.vision_backbone"): v
                for k, v in sam3_image_ckpt.items()
                if "backbone.vision_backbone" in k
            }
        )
        sam3_image_ckpt.update(
            {
                k.replace("tracker.transformer.encoder", "memory_attention"): v
                for k, v in ckpt.items()
                if "tracker.transformer" in k
            }
        )
        sam3_image_ckpt.update(
            {
                k.replace("tracker.maskmem_backbone", "memory_encoder"): v
                for k, v in ckpt.items()
                if "tracker.maskmem_backbone" in k
            }
        )
        sam3_image_ckpt.update({k.replace("tracker.", ""): v for k, v in ckpt.items() if "tracker." in k})
    model.load_state_dict(sam3_image_ckpt, strict=False)
    return model