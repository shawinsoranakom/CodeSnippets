def convert_dpt_checkpoint(model_name, pytorch_dump_folder_path, push_to_hub, verify_logits):
    """
    Copy/paste/tweak model's weights to our DPT structure.
    """

    # define DPT configuration
    config = get_dpt_config(model_name)

    model_name_to_repo = {
        "depth-anything-small": "LiheYoung/depth_anything_vits14",
        "depth-anything-base": "LiheYoung/depth_anything_vitb14",
        "depth-anything-large": "LiheYoung/depth_anything_vitl14",
        "depth-anything-v2-small": "depth-anything/Depth-Anything-V2-Small",
        "depth-anything-v2-base": "depth-anything/Depth-Anything-V2-Base",
        "depth-anything-v2-large": "depth-anything/Depth-Anything-V2-Large",
        "depth-anything-v2-metric-indoor-small": "depth-anything/Depth-Anything-V2-Metric-Hypersim-Small",
        "depth-anything-v2-metric-indoor-base": "depth-anything/Depth-Anything-V2-Metric-Hypersim-Base",
        "depth-anything-v2-metric-indoor-large": "depth-anything/Depth-Anything-V2-Metric-Hypersim-Large",
        "depth-anything-v2-metric-outdoor-small": "depth-anything/Depth-Anything-V2-Metric-VKITTI-Small",
        "depth-anything-v2-metric-outdoor-base": "depth-anything/Depth-Anything-V2-Metric-VKITTI-Base",
        "depth-anything-v2-metric-outdoor-large": "depth-anything/Depth-Anything-V2-Metric-VKITTI-Large",
    }

    # load original state_dict
    repo_id = model_name_to_repo[model_name]
    filename = name_to_checkpoint[model_name]
    filepath = hf_hub_download(
        repo_id=repo_id,
        filename=f"{filename}",
    )

    state_dict = torch.load(filepath, map_location="cpu", weights_only=True)
    # rename keys
    rename_keys = create_rename_keys(config)
    for src, dest in rename_keys:
        rename_key(state_dict, src, dest)
    # read in qkv matrices
    read_in_q_k_v(state_dict, config)

    # load HuggingFace model
    model = DepthAnythingForDepthEstimation(config)
    model.load_state_dict(state_dict)
    model.eval()

    processor = DPTImageProcessor(
        do_resize=True,
        size={"height": 518, "width": 518},
        ensure_multiple_of=14,
        keep_aspect_ratio=True,
        do_rescale=True,
        do_normalize=True,
        image_mean=[0.485, 0.456, 0.406],
        image_std=[0.229, 0.224, 0.225],
    )

    url = "http://images.cocodataset.org/val2017/000000039769.jpg"
    with httpx.stream("GET", url) as response:
        image = Image.open(BytesIO(response.read()))

    pixel_values = processor(image, return_tensors="pt").pixel_values

    # Verify forward pass
    with torch.no_grad():
        outputs = model(pixel_values)
        predicted_depth = outputs.predicted_depth

    print("Shape of predicted depth:", predicted_depth.shape)
    print("First values:", predicted_depth[0, :3, :3])

    # assert logits
    if verify_logits:
        expected_shape = torch.Size([1, 518, 686])
        if model_name == "depth-anything-small":
            expected_slice = torch.tensor(
                [[8.8204, 8.6468, 8.6195], [8.3313, 8.6027, 8.7526], [8.6526, 8.6866, 8.7453]],
            )
        elif model_name == "depth-anything-base":
            expected_slice = torch.tensor(
                [[26.3997, 26.3004, 26.3928], [26.2260, 26.2092, 26.3427], [26.0719, 26.0483, 26.1254]],
            )
        elif model_name == "depth-anything-large":
            expected_slice = torch.tensor(
                [[87.9968, 87.7493, 88.2704], [87.1927, 87.6611, 87.3640], [86.7789, 86.9469, 86.7991]]
            )
        elif model_name == "depth-anything-v2-small":
            expected_slice = torch.tensor(
                [[2.6751, 2.6211, 2.6571], [2.5820, 2.6138, 2.6271], [2.6160, 2.6141, 2.6306]]
            )
        elif model_name == "depth-anything-v2-base":
            expected_slice = torch.tensor(
                [[4.3576, 4.3723, 4.3908], [4.3231, 4.3146, 4.3611], [4.3016, 4.3170, 4.3121]]
            )
        elif model_name == "depth-anything-v2-large":
            expected_slice = torch.tensor(
                [[162.2751, 161.8504, 162.8788], [160.3138, 160.8050, 161.9835], [159.3812, 159.9884, 160.0768]]
            )
        elif model_name == "depth-anything-v2-metric-indoor-small":
            expected_slice = torch.tensor(
                [[1.3349, 1.2946, 1.2801], [1.2793, 1.2337, 1.2899], [1.2629, 1.2218, 1.2476]]
            )
        elif model_name == "depth-anything-v2-metric-indoor-base":
            expected_slice = torch.tensor(
                [[1.4601, 1.3824, 1.4904], [1.5031, 1.4349, 1.4274], [1.4570, 1.4578, 1.4200]]
            )
        elif model_name == "depth-anything-v2-metric-indoor-large":
            expected_slice = torch.tensor(
                [[1.5040, 1.5019, 1.5218], [1.5087, 1.5195, 1.5149], [1.5437, 1.5128, 1.5252]]
            )
        elif model_name == "depth-anything-v2-metric-outdoor-small":
            expected_slice = torch.tensor(
                [[9.5804, 8.0339, 7.7386], [7.9890, 7.2464, 7.7149], [7.7021, 7.2330, 7.3304]]
            )
        elif model_name == "depth-anything-v2-metric-outdoor-base":
            expected_slice = torch.tensor(
                [[10.2916, 9.0933, 8.8622], [9.1964, 9.3393, 9.0644], [8.9618, 9.4201, 9.2262]]
            )
        elif model_name == "depth-anything-v2-metric-outdoor-large":
            expected_slice = torch.tensor(
                [[14.0137, 13.3627, 13.1080], [13.2522, 13.3943, 13.3705], [13.0581, 13.4505, 13.3925]]
            )
        else:
            raise ValueError("Not supported")

        assert predicted_depth.shape == torch.Size(expected_shape)
        assert torch.allclose(predicted_depth[0, :3, :3], expected_slice, atol=1e-4)
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