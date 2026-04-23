def test_visual_full(freeze_vision_tower: bool, freeze_multi_modal_projector: bool, freeze_language_model: bool):
    model_args = ModelArguments(model_name_or_path="Qwen/Qwen2-VL-2B-Instruct")
    finetuning_args = FinetuningArguments(
        finetuning_type="full",
        freeze_vision_tower=freeze_vision_tower,
        freeze_multi_modal_projector=freeze_multi_modal_projector,
        freeze_language_model=freeze_language_model,
    )
    config = AutoConfig.from_pretrained(model_args.model_name_or_path)
    with torch.device("meta"):
        model = AutoModelForImageTextToText.from_config(config)

    model = init_adapter(config, model, model_args, finetuning_args, is_trainable=True)
    for name, param in model.named_parameters():
        if any(key in name for key in ["visual.patch_embed", "visual.blocks"]):
            assert param.requires_grad != freeze_vision_tower
        elif "visual.merger" in name:
            assert param.requires_grad != freeze_multi_modal_projector
        else:
            assert param.requires_grad != freeze_language_model