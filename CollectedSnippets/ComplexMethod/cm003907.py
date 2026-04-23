def convert_omdet_turbo_checkpoint(args):
    model_name = args.model_name
    pytorch_dump_folder_path = args.pytorch_dump_folder_path
    push_to_hub = args.push_to_hub
    use_timm_backbone = args.use_timm_backbone

    checkpoint_mapping = {
        "omdet-turbo-tiny": [
            "https://huggingface.co/omlab/OmDet-Turbo_tiny_SWIN_T/resolve/main/OmDet-Turbo_tiny_SWIN_T.pth",
            "https://huggingface.co/omlab/OmDet-Turbo_tiny_SWIN_T/resolve/main/ViT-B-16.pt",
        ],
    }
    # Define default OmDetTurbo configuration
    config = get_omdet_turbo_config(model_name, use_timm_backbone)

    # Load original checkpoint
    checkpoint_url = checkpoint_mapping[model_name]
    original_state_dict_vision = torch.hub.load_state_dict_from_url(checkpoint_url[0], map_location="cpu")["model"]
    original_state_dict_vision = {k.replace("module.", ""): v for k, v in original_state_dict_vision.items()}

    # Rename keys
    new_state_dict = original_state_dict_vision.copy()
    rename_keys_vision = create_rename_keys_vision(new_state_dict, config)

    rename_keys_language = create_rename_keys_language(new_state_dict)

    for src, dest in rename_keys_vision:
        rename_key(new_state_dict, src, dest)

    for src, dest in rename_keys_language:
        rename_key(new_state_dict, src, dest)

    if not use_timm_backbone:
        read_in_q_k_v_vision(new_state_dict, config)
    read_in_q_k_v_text(new_state_dict, config)
    read_in_q_k_v_encoder(new_state_dict, config)
    read_in_q_k_v_decoder(new_state_dict, config)
    # add "model" prefix to all keys
    new_state_dict = {f"model.{k}": v for k, v in new_state_dict.items()}

    # Load HF model
    model = OmDetTurboForObjectDetection(config)
    model.eval()
    missing_keys, unexpected_keys = model.load_state_dict(new_state_dict, strict=False)
    print("Missing keys:", missing_keys)
    print("Unexpected keys:", unexpected_keys)

    image_processor = DetrImageProcessor(
        size={"height": config.backbone_image_size, "width": config.backbone_image_size},
        do_rescale=False,
        image_mean=IMAGE_MEAN,
        image_std=IMAGE_STD,
        do_pad=False,
    )
    tokenizer = CLIPTokenizer.from_pretrained("openai/clip-vit-base-patch32")
    processor = OmDetTurboProcessor(image_processor=image_processor, tokenizer=tokenizer)

    # end-to-end consistency test
    run_test(model, processor)

    if pytorch_dump_folder_path is not None:
        model.save_pretrained(pytorch_dump_folder_path)
        processor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        model.push_to_hub(f"omlab/{model_name}")
        processor.push_to_hub(f"omlab/{model_name}")