def _freeze_model_parameters(model: Any, finetuning_args: "FinetuningArguments"):
    """Freeze model parameters for qwen_vl series models based on finetuning arguments."""
    if getattr(model.config, "hf_model_type", None) not in ["qwen2_vl", "qwen2_5_vl", "qwen3_vl", "qwen3_vl_moe", "qwen3_5", "qwen3_5_moe"]:
        return

    params_to_freeze = []
    if finetuning_args.freeze_vision_tower:
        params_to_freeze.extend(["vision_model.blocks", "vision_model.patch_embed"])
        if getattr(model.config, "hf_model_type", None) in ["qwen3_vl", "qwen3_vl_moe", "qwen3_5", "qwen3_5_moe"]:
            params_to_freeze.extend(["vision_model.pos_embed"])

    if finetuning_args.freeze_multi_modal_projector:
        params_to_freeze.extend(["vision_model.merger"])

    if finetuning_args.freeze_language_model:
        params_to_freeze.extend(["embedding", "decoder", "output_layer"])

    if params_to_freeze:
        for name, p in model.named_parameters():
            if any(name.startswith(k) for k in params_to_freeze):
                p.requires_grad_(False)