def convert_sam2_checkpoint(model_name, checkpoint_path, pytorch_dump_folder, push_to_hub):
    config = get_config(model_name)

    state_dict = torch.load(checkpoint_path, map_location="cpu")["model"]
    state_dict = replace_keys(state_dict)

    image_processor = Sam2ImageProcessorFast()
    processor = Sam2Processor(image_processor=image_processor)
    hf_model = Sam2Model(config)
    hf_model.eval()

    device = "cuda" if torch.cuda.is_available() else "cpu"

    missing_keys, unexpected_keys = hf_model.load_state_dict(state_dict, strict=False)
    hf_model = hf_model.to(device)
    for pattern in Sam2Model._keys_to_ignore_on_load_unexpected:
        unexpected_keys = [k for k in unexpected_keys if re.search(pattern, k) is None]
    if missing_keys or unexpected_keys:
        print("Missing keys:", missing_keys)
        print("Unexpected keys:", unexpected_keys)
        raise ValueError("Missing or unexpected keys in the state dict")

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

    if model_name == "sam2.1_hiera_tiny":
        assert torch.allclose(scores, torch.tensor([0.0316, 0.9647, 0.1029]).cuda(), atol=1e-2)
    elif model_name == "sam2.1_hiera_small":
        assert torch.allclose(scores, torch.tensor([0.9664, 0.1494, 0.0456]).cuda(), atol=1e-2)
    elif model_name == "sam2.1_hiera_base_plus":
        assert torch.allclose(scores, torch.tensor([0.0361, 0.9775, 0.1307]).cuda(), atol=1e-2)
    elif model_name == "sam2.1_hiera_large":
        assert torch.allclose(scores, torch.tensor([0.9648, 0.0371, 0.1898]).cuda(), atol=1e-2)
    elif model_name == "sam2_hiera_tiny":
        assert torch.allclose(scores, torch.tensor([0.0439, 0.9567, 0.1415]).cuda(), atol=1e-2)
    elif model_name == "sam2_hiera_small":
        assert torch.allclose(scores, torch.tensor([0.9593, 0.1633, 0.0392]).cuda(), atol=1e-2)
    elif model_name == "sam2_hiera_base_plus":
        assert torch.allclose(scores, torch.tensor([0.0423, 0.9815, 0.0897]).cuda(), atol=1e-2)
    elif model_name == "sam2_hiera_large":
        assert torch.allclose(scores, torch.tensor([0.9514, 0.0535, 0.1787]).cuda(), atol=1e-2)
    else:
        raise ValueError(f"Model {model_name} not supported")

    if pytorch_dump_folder is not None:
        processor.save_pretrained(pytorch_dump_folder)
        hf_model.save_pretrained(pytorch_dump_folder)

    if push_to_hub:
        repo_id = f"danelcsb/{pytorch_dump_folder.split('/')[-1]}"
        processor.push_to_hub(repo_id)
        hf_model.push_to_hub(repo_id)