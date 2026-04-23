def convert_dpt_checkpoint(model_name, pytorch_dump_folder_path, push_to_hub):
    """
    Copy/paste/tweak model's weights to our DPT structure.
    """

    name_to_url = {
        "dpt-beit-large-512": "https://github.com/isl-org/MiDaS/releases/download/v3_1/dpt_beit_large_512.pt",
        "dpt-beit-large-384": "https://github.com/isl-org/MiDaS/releases/download/v3_1/dpt_beit_large_384.pt",
        "dpt-beit-base-384": "https://github.com/isl-org/MiDaS/releases/download/v3_1/dpt_beit_base_384.pt",
    }

    # define DPT configuration based on URL
    checkpoint_url = name_to_url[model_name]
    config, image_size = get_dpt_config(model_name)
    # load original state_dict from URL
    state_dict = torch.hub.load_state_dict_from_url(checkpoint_url, map_location="cpu")
    # remove certain keys
    remove_ignore_keys_(state_dict)
    # rename keys
    rename_keys = create_rename_keys(config)
    for src, dest in rename_keys:
        rename_key(state_dict, src, dest)
    # read in qkv matrices
    read_in_q_k_v(state_dict, config)

    # load HuggingFace model
    model = DPTForDepthEstimation(config)
    missing_keys, unexpected_keys = model.load_state_dict(state_dict, strict=False)
    print("Missing keys:", missing_keys)
    print("Unexpected keys:", unexpected_keys)
    assert missing_keys == []
    # assert unexpected_keys == ["pretrained.model.fc_norm.weight", "pretrained.model.fc_norm.bias"]
    model.eval()

    # Check outputs on an image
    # We set `keep_aspect_ratio=False` as our current BEiT does not support arbitrary window sizes
    processor = DPTImageProcessor(
        size={"height": image_size, "width": image_size}, keep_aspect_ratio=False, ensure_multiple_of=32
    )

    image = prepare_img()
    pixel_values = processor(image, return_tensors="pt").pixel_values

    print("First values of pixel values:", pixel_values[0, 0, :3, :3])
    print("Mean of pixel values:", pixel_values.mean().item())
    print("Shape of pixel values:", pixel_values.shape)

    from PIL import Image
    from torchvision import transforms

    url = "http://images.cocodataset.org/val2017/000000039769.jpg"
    with httpx.stream("GET", url) as response:
        image = Image.open(BytesIO(response.read()))

    transforms = transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
        ]
    )
    pixel_values = transforms(image).unsqueeze(0)

    # forward pass
    with torch.no_grad():
        outputs = model(pixel_values)

    predicted_depth = outputs.predicted_depth

    print("Shape of predicted depth:", predicted_depth.shape)
    print("First values of predicted depth:", predicted_depth[0, :3, :3])

    # assert logits
    # TODO there's still a small difference with the original logits
    if model_name == "dpt-beit-large-512":
        # OK, checked
        expected_shape = torch.Size([1, 512, 512])
        expected_slice = torch.tensor(
            [[2804.6260, 2792.5708, 2812.9263], [2772.0288, 2780.1118, 2796.2529], [2748.1094, 2766.6558, 2766.9834]]
        )
    elif model_name == "dpt-beit-large-384":
        # OK, checked
        expected_shape = torch.Size([1, 384, 384])
        expected_slice = torch.tensor(
            [[1783.2273, 1780.5729, 1792.6453], [1759.9817, 1765.5359, 1778.5002], [1739.1633, 1754.7903, 1757.1990]],
        )
    elif model_name == "dpt-beit-base-384":
        # OK, checked
        expected_shape = torch.Size([1, 384, 384])
        expected_slice = torch.tensor(
            [[2898.4482, 2891.3750, 2904.8079], [2858.6685, 2877.2615, 2894.4507], [2842.1235, 2854.1023, 2861.6328]],
        )

    assert predicted_depth.shape == torch.Size(expected_shape)
    assert torch.allclose(predicted_depth[0, :3, :3], expected_slice)
    print("Looks ok!")

    if pytorch_dump_folder_path is not None:
        Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
        print(f"Saving model and processor to {pytorch_dump_folder_path}")
        model.save_pretrained(pytorch_dump_folder_path)
        processor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        print("Pushing model and processor to hub...")
        model.push_to_hub(repo_id=f"nielsr/{model_name}")
        processor.push_to_hub(repo_id=f"nielsr/{model_name}")