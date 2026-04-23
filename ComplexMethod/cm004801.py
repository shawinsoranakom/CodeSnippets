def convert_dpt_checkpoint(model_name, pytorch_dump_folder_path, verify_logits, push_to_hub):
    """
    Copy/paste/tweak model's weights to our DPT structure.
    """

    name_to_url = {
        "dpt-swinv2-tiny-256": "https://github.com/isl-org/MiDaS/releases/download/v3_1/dpt_swin2_tiny_256.pt",
        "dpt-swinv2-base-384": "https://github.com/isl-org/MiDaS/releases/download/v3_1/dpt_swin2_base_384.pt",
        "dpt-swinv2-large-384": "https://github.com/isl-org/MiDaS/releases/download/v3_1/dpt_swin2_large_384.pt",
    }

    # define DPT configuration based on URL
    checkpoint_url = name_to_url[model_name]
    config, image_size = get_dpt_config(model_name)
    # load original state_dict from URL
    state_dict = torch.hub.load_state_dict_from_url(checkpoint_url, map_location="cpu")

    # load HuggingFace model
    model = DPTForDepthEstimation(config)

    # remove certain keys
    remove_ignore_keys_(state_dict)
    # rename keys
    rename_keys = create_rename_keys(config)
    for src, dest in rename_keys:
        rename_key(state_dict, src, dest)
    # read in qkv matrices
    read_in_q_k_v(state_dict, config, model)

    missing_keys, unexpected_keys = model.load_state_dict(state_dict, strict=False)
    print("Missing keys:", missing_keys)
    print("Unexpected keys:", unexpected_keys)
    model.eval()

    # Check outputs on an image
    processor = DPTImageProcessor(size={"height": image_size, "width": image_size})

    image = prepare_img()
    processor(image, return_tensors="pt")

    if verify_logits:
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
        if model_name == "dpt-swinv2-base-384":
            # OK, checked
            expected_shape = torch.Size([1, 384, 384])
            expected_slice = torch.tensor(
                [
                    [1998.5575, 1997.3887, 2009.2981],
                    [1952.8607, 1979.6488, 2001.0854],
                    [1953.7697, 1961.7711, 1968.8904],
                ],
            )
        elif model_name == "dpt-swinv2-tiny-256":
            # OK, checked
            expected_shape = torch.Size([1, 256, 256])
            expected_slice = torch.tensor(
                [[978.9163, 976.5215, 978.5349], [974.1859, 971.7249, 975.8046], [971.3419, 970.3118, 971.6830]],
            )
        elif model_name == "dpt-swinv2-large-384":
            # OK, checked
            expected_shape = torch.Size([1, 384, 384])
            expected_slice = torch.tensor(
                [
                    [1203.7206, 1200.1495, 1197.8234],
                    [1196.2484, 1183.5033, 1186.4640],
                    [1178.8131, 1182.3260, 1174.3975],
                ],
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
        model.push_to_hub(repo_id=f"Intel/{model_name}")
        processor.push_to_hub(repo_id=f"Intel/{model_name}")