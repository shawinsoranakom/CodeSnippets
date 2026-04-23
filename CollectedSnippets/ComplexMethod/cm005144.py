def convert_dpt_checkpoint(model_name, pytorch_dump_folder_path, push_to_hub, verify_logits):
    """
    Copy/paste/tweak model's weights to our DPT structure.
    """

    # define DPT configuration
    config = get_dpt_config(model_name)

    model_name_to_repo = {
        "prompt-depth-anything-vits": "depth-anything/prompt-depth-anything-vits",
        "prompt-depth-anything-vits-transparent": "depth-anything/prompt-depth-anything-vits-transparent",
        "prompt-depth-anything-vitl": "depth-anything/prompt-depth-anything-vitl",
    }

    # load original state_dict
    repo_id = model_name_to_repo[model_name]
    filename = name_to_checkpoint[model_name]
    filepath = hf_hub_download(
        repo_id=repo_id,
        filename=f"{filename}",
    )

    state_dict = torch.load(filepath, map_location="cpu", weights_only=True)["state_dict"]
    state_dict = {key[9:]: state_dict[key] for key in state_dict}

    # Convert state dict using mappings
    key_mapping = convert_old_keys_to_new_keys(state_dict.keys())
    new_state_dict = {}
    for key, value in state_dict.items():
        new_key = key_mapping[key]
        transformed_value = transform_qkv_weights(new_key, value, config)
        if isinstance(transformed_value, dict):
            new_state_dict.update(transformed_value)
        else:
            new_state_dict[new_key] = transformed_value

    # load HuggingFace model
    model = PromptDepthAnythingForDepthEstimation(config)
    model.load_state_dict(new_state_dict, strict=False)
    model.eval()

    processor = PromptDepthAnythingImageProcessor(
        do_resize=True,
        size=756,
        ensure_multiple_of=14,
        keep_aspect_ratio=True,
        do_rescale=True,
        do_normalize=True,
        image_mean=[0.485, 0.456, 0.406],
        image_std=[0.229, 0.224, 0.225],
    )
    url = "https://github.com/DepthAnything/PromptDA/blob/main/assets/example_images/image.jpg?raw=true"
    with httpx.stream("GET", url) as response:
        image = Image.open(BytesIO(response.read()))

    prompt_depth_url = (
        "https://github.com/DepthAnything/PromptDA/blob/main/assets/example_images/arkit_depth.png?raw=true"
    )
    with httpx.stream("GET", prompt_depth_url) as response:
        prompt_depth = Image.open(BytesIO(response.read()))

    inputs = processor(image, return_tensors="pt", prompt_depth=prompt_depth)

    # Verify forward pass
    with torch.no_grad():
        outputs = model(**inputs)
        predicted_depth = outputs.predicted_depth

    print("Shape of predicted depth:", predicted_depth.shape)
    print("First values:", predicted_depth[0, :3, :3])

    # assert logits
    if verify_logits:
        expected_shape = torch.Size([1, 756, 1008])
        if model_name == "prompt-depth-anything-vits":
            expected_slice = torch.tensor(
                [[3.0100, 3.0016, 3.0219], [3.0046, 3.0137, 3.0275], [3.0083, 3.0191, 3.0292]]
            )
        elif model_name == "prompt-depth-anything-vits-transparent":
            expected_slice = torch.tensor(
                [[3.0058, 3.0397, 3.0460], [3.0314, 3.0393, 3.0504], [3.0326, 3.0465, 3.0545]]
            )
        elif model_name == "prompt-depth-anything-vitl":
            expected_slice = torch.tensor(
                [[3.1336, 3.1358, 3.1363], [3.1368, 3.1267, 3.1414], [3.1397, 3.1385, 3.1448]]
            )
        else:
            raise ValueError("Not supported")
        assert predicted_depth.shape == torch.Size(expected_shape)
        assert torch.allclose(predicted_depth[0, :3, :3], expected_slice, atol=5e-3)  # 5mm tolerance
        print("Looks ok!")

    if pytorch_dump_folder_path is not None:
        Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
        print(f"Saving model and processor to {pytorch_dump_folder_path}")
        model.save_pretrained(pytorch_dump_folder_path)
        processor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        print("Pushing model and processor to hub...")
        model.push_to_hub(repo_id=f"{model_name.title()}-hf")
        processor.push_to_hub(repo_id=f"{model_name.title()}-hf")