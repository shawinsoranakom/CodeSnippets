def convert_dpt_checkpoint(model_name, pytorch_dump_folder_path, push_to_hub, verify_logits):
    """
    Copy/paste/tweak model's weights to our DPT structure.
    """

    # define DPT configuration based on URL
    checkpoint_url = name_to_url[model_name]
    config = get_dpt_config(model_name)

    # load original DPT state_dict from URL
    print("URL:", checkpoint_url)
    dpt_state_dict = torch.hub.load_state_dict_from_url(checkpoint_url, map_location="cpu")["state_dict"]
    # rename keys
    rename_keys = create_rename_keys_dpt(config)
    for src, dest in rename_keys:
        rename_key(dpt_state_dict, src, dest)

    # load original backbone state_dict from URL
    if "small" in model_name:
        original_model = torch.hub.load("facebookresearch/dinov2", "dinov2_vits14")
    elif "base" in model_name:
        original_model = torch.hub.load("facebookresearch/dinov2", "dinov2_vitb14")
    elif "large" in model_name:
        original_model = torch.hub.load("facebookresearch/dinov2", "dinov2_vitl14")
    elif "giant" in model_name:
        original_model = torch.hub.load("facebookresearch/dinov2", "dinov2_vitg14")
    else:
        raise NotImplementedError("To do")
    original_model.eval()
    backbone_state_dict = original_model.state_dict()

    # rename keys
    rename_keys = create_rename_keys_backbone(config)
    for src, dest in rename_keys:
        rename_key(backbone_state_dict, src, dest)

    # read in qkv matrices
    read_in_q_k_v(backbone_state_dict, config)

    for key, val in backbone_state_dict.copy().items():
        val = backbone_state_dict.pop(key)
        if "w12" in key:
            key = key.replace("w12", "weights_in")
        if "w3" in key:
            key = key.replace("w3", "weights_out")
        backbone_state_dict[key] = val

    # merge state_dicts
    state_dict = {**backbone_state_dict, **dpt_state_dict}

    # load HuggingFace model
    model = DPTForDepthEstimation(config)
    missing_keys, unexpected_keys = model.load_state_dict(state_dict, strict=False)
    print("Missing keys:", missing_keys)
    print("Unexpected keys:", unexpected_keys)
    assert missing_keys == [
        "neck.fusion_stage.layers.0.residual_layer1.convolution1.weight",
        "neck.fusion_stage.layers.0.residual_layer1.convolution2.weight",
    ]
    model.eval()

    # Verify image processor
    processor = DPTImageProcessor(
        do_resize=False,
        do_rescale=False,
        do_pad=True,
        size_divisor=14,
        do_normalize=True,
        image_mean=(123.675, 116.28, 103.53),
        image_std=(58.395, 57.12, 57.375),
    )

    image = prepare_img()
    pixel_values = processor(image, return_tensors="pt").pixel_values.float()
    original_pixel_values = get_original_pixel_values(image)

    assert torch.allclose(pixel_values, original_pixel_values)

    # Verify forward pass
    with torch.no_grad():
        outputs = model(pixel_values)

    predicted_depth = outputs.predicted_depth

    print("Shape of predicted depth:", predicted_depth.shape)
    print("First values of predicted depth:", predicted_depth[0, :3, :3])

    # assert logits
    if verify_logits:
        if model_name == "dpt-dinov2-small-nyu":
            expected_shape = torch.Size([1, 576, 736])
            expected_slice = torch.tensor(
                [[3.3576, 3.4741, 3.4345], [3.4324, 3.5012, 3.2775], [3.2560, 3.3563, 3.2354]]
            )

        assert predicted_depth.shape == torch.Size(expected_shape)
        assert torch.allclose(predicted_depth[0, :3, :3], expected_slice, atol=1e-5)
        print("Looks ok!")

    if pytorch_dump_folder_path is not None:
        Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
        print(f"Saving model and processor to {pytorch_dump_folder_path}")
        model.save_pretrained(pytorch_dump_folder_path)
        processor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        print("Pushing model and processor to hub...")
        model.push_to_hub(repo_id=f"facebook/{model_name}")
        processor.push_to_hub(repo_id=f"facebook/{model_name}")