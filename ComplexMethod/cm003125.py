def convert_dpt_checkpoint(model_name, pytorch_dump_folder_path, push_to_hub, verify_logits):
    config = get_dpt_config(model_name)

    repo_id = "xingyang1/Distill-Any-Depth"
    filepath = hf_hub_download(repo_id=repo_id, filename=name_to_checkpoint[model_name])
    state_dict = load_file(filepath)

    converted_state_dict = convert_keys(state_dict, config)

    model = DepthAnythingForDepthEstimation(config)
    model.load_state_dict(converted_state_dict)
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

    with torch.no_grad():
        outputs = model(pixel_values)
        predicted_depth = outputs.predicted_depth

    print("Shape of predicted depth:", predicted_depth.shape)
    print("First values:", predicted_depth[0, :3, :3])

    if verify_logits:
        print("Verifying logits...")
        expected_shape = torch.Size([1, 518, 686])

        if model_name == "distill-any-depth-small":
            expected_slice = torch.tensor(
                [[2.5653, 2.5249, 2.5570], [2.4897, 2.5235, 2.5355], [2.5255, 2.5261, 2.5422]]
            )
        elif model_name == "distill-any-depth-base":
            expected_slice = torch.tensor(
                [[4.8976, 4.9075, 4.9403], [4.8872, 4.8906, 4.9448], [4.8712, 4.8898, 4.8838]]
            )
        elif model_name == "distill-any-depth-large":
            expected_slice = torch.tensor(
                [[55.1067, 51.1828, 51.6803], [51.9098, 50.7529, 51.4494], [50.1745, 50.5491, 50.8818]]
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