def convert_edgetam_checkpoint(model_name, checkpoint_path, pytorch_dump_folder, push_to_hub, run_sanity_check):
    config = get_config(model_name)

    state_dict = torch.load(checkpoint_path, map_location="cpu")["model"]
    state_dict = replace_keys(state_dict)

    image_processor = Sam2ImageProcessorFast()
    processor = Sam2Processor(image_processor=image_processor)
    hf_model = EdgeTamModel(config)
    hf_model.eval()

    device = "cuda" if torch.cuda.is_available() else "cpu"

    missing_keys, unexpected_keys = hf_model.load_state_dict(state_dict, strict=False)
    hf_model = hf_model.to(device)
    for pattern in EdgeTamModel._keys_to_ignore_on_load_unexpected:
        unexpected_keys = [k for k in unexpected_keys if re.search(pattern, k) is None]
    if missing_keys or unexpected_keys:
        print("Missing keys:", missing_keys)
        print("Unexpected keys:", unexpected_keys)
        raise ValueError("Missing or unexpected keys in the state dict")

    if run_sanity_check:
        url = "https://huggingface.co/ybelkada/segment-anything/resolve/main/assets/car.png"
        with httpx.stream("GET", url) as response:
            raw_image = Image.open(BytesIO(response.read())).convert("RGB")

        input_points = [[[[1000, 600]]]]
        input_labels = [[[1]]]

        inputs = processor(
            images=np.array(raw_image), input_points=input_points, input_labels=input_labels, return_tensors="pt"
        ).to(device)

        with torch.no_grad():
            output = hf_model(**inputs)
        scores = output.iou_scores.squeeze()

        assert torch.allclose(scores, torch.tensor([0.0356, 0.2141, 0.9707]).cuda(), atol=1e-3)

    if pytorch_dump_folder is not None:
        processor.save_pretrained(pytorch_dump_folder)
        hf_model.save_pretrained(pytorch_dump_folder)

    if push_to_hub:
        repo_id = f"yonigozlan/{pytorch_dump_folder.split('/')[-1]}"
        processor.push_to_hub(repo_id)
        hf_model.push_to_hub(repo_id)