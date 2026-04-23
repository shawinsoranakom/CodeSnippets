def convert_timesformer_checkpoint(checkpoint_url, pytorch_dump_folder_path, model_name, push_to_hub):
    config = get_timesformer_config(model_name)

    model = TimesformerForVideoClassification(config)

    # download original checkpoint, hosted on Google Drive
    output = "pytorch_model.bin"
    gdown.cached_download(checkpoint_url, output, quiet=False)
    files = torch.load(output, map_location="cpu", weights_only=True)
    if "model" in files:
        state_dict = files["model"]
    elif "module" in files:
        state_dict = files["module"]
    else:
        state_dict = files["model_state"]
    new_state_dict = convert_state_dict(state_dict, config)

    model.load_state_dict(new_state_dict)
    model.eval()

    # verify model on basic input
    image_processor = VideoMAEImageProcessor(image_mean=[0.5, 0.5, 0.5], image_std=[0.5, 0.5, 0.5])
    video = prepare_video()
    inputs = image_processor(video[:8], return_tensors="pt")

    outputs = model(**inputs)
    logits = outputs.logits

    model_names = [
        # Kinetics-400 checkpoints (hr = high resolution input of 448px instead of 224px)
        "timesformer-base-finetuned-k400",
        "timesformer-large-finetuned-k400",
        "timesformer-hr-finetuned-k400",
        # Kinetics-600 checkpoints (hr = high resolution input of 448px instead of 224px)
        "timesformer-base-finetuned-k600",
        "timesformer-large-finetuned-k600",
        "timesformer-hr-finetuned-k600",
        # Something-Something-v2 checkpoints (hr = high resolution input of 448px instead of 224px)
        "timesformer-base-finetuned-ssv2",
        "timesformer-large-finetuned-ssv2",
        "timesformer-hr-finetuned-ssv2",
    ]

    # NOTE: logits were tested with image_mean and image_std equal to [0.5, 0.5, 0.5] and [0.5, 0.5, 0.5]
    if model_name == "timesformer-base-finetuned-k400":
        expected_shape = torch.Size([1, 400])
        expected_slice = torch.tensor([-0.3016, -0.7713, -0.4205])
    elif model_name == "timesformer-base-finetuned-k600":
        expected_shape = torch.Size([1, 600])
        expected_slice = torch.tensor([-0.7267, -0.7466, 3.2404])
    elif model_name == "timesformer-base-finetuned-ssv2":
        expected_shape = torch.Size([1, 174])
        expected_slice = torch.tensor([-0.9059, 0.6433, -3.1457])
    elif model_name == "timesformer-large-finetuned-k400":
        expected_shape = torch.Size([1, 400])
        expected_slice = torch.tensor([0, 0, 0])
    elif model_name == "timesformer-large-finetuned-k600":
        expected_shape = torch.Size([1, 600])
        expected_slice = torch.tensor([0, 0, 0])
    elif model_name == "timesformer-large-finetuned-ssv2":
        expected_shape = torch.Size([1, 174])
        expected_slice = torch.tensor([0, 0, 0])
    elif model_name == "timesformer-hr-finetuned-k400":
        expected_shape = torch.Size([1, 400])
        expected_slice = torch.tensor([-0.9617, -3.7311, -3.7708])
    elif model_name == "timesformer-hr-finetuned-k600":
        expected_shape = torch.Size([1, 600])
        expected_slice = torch.tensor([2.5273, 0.7127, 1.8848])
    elif model_name == "timesformer-hr-finetuned-ssv2":
        expected_shape = torch.Size([1, 174])
        expected_slice = torch.tensor([-3.6756, -0.7513, 0.7180])
    else:
        raise ValueError(f"Model name not supported. Should be one of {model_names}")

    # verify logits
    assert logits.shape == expected_shape
    assert torch.allclose(logits[0, :3], expected_slice, atol=1e-4)
    print("Logits ok!")

    if pytorch_dump_folder_path is not None:
        print(f"Saving model and image processor to {pytorch_dump_folder_path}")
        image_processor.save_pretrained(pytorch_dump_folder_path)
        model.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        print("Pushing to the hub...")
        model.push_to_hub(f"fcakyon/{model_name}")