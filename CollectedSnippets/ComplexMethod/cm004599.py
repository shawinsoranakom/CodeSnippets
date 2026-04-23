def convert_sam_checkpoint(model_name, checkpoint_path, pytorch_dump_folder, push_to_hub):
    config = get_config(model_name)

    state_dict = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    state_dict = replace_keys(state_dict)

    image_processor = SamImageProcessor()
    processor = SamProcessor(image_processor=image_processor)
    hf_model = SamModel(config)
    hf_model.eval()

    device = "cuda" if torch.cuda.is_available() else "cpu"

    hf_model.load_state_dict(state_dict)
    hf_model = hf_model.to(device)

    url = "https://huggingface.co/ybelkada/segment-anything/resolve/main/assets/car.png"
    with httpx.stream("GET", url) as response:
        raw_image = Image.open(BytesIO(response.read())).convert("RGB")

    input_points = [[[500, 375]]]
    input_labels = [[1]]

    inputs = processor(images=np.array(raw_image), return_tensors="pt").to(device)

    with torch.no_grad():
        output = hf_model(**inputs)
    scores = output.iou_scores.squeeze()

    if model_name == "sam_vit_b_01ec64":
        inputs = processor(
            images=np.array(raw_image), input_points=input_points, input_labels=input_labels, return_tensors="pt"
        ).to(device)

        with torch.no_grad():
            output = hf_model(**inputs)
            scores = output.iou_scores.squeeze()

    elif model_name == "sam_vit_h_4b8939":
        inputs = processor(
            images=np.array(raw_image), input_points=input_points, input_labels=input_labels, return_tensors="pt"
        ).to(device)

        with torch.no_grad():
            output = hf_model(**inputs)
        scores = output.iou_scores.squeeze()

        assert scores[-1].item() == 0.9712603092193604

        input_boxes = ((75, 275, 1725, 850),)

        inputs = processor(images=np.array(raw_image), input_boxes=input_boxes, return_tensors="pt").to(device)

        with torch.no_grad():
            output = hf_model(**inputs)
        scores = output.iou_scores.squeeze()

        assert scores[-1].item() == 0.8686015605926514

        # Test with 2 points and 1 image.
        input_points = [[[400, 650], [800, 650]]]
        input_labels = [[1, 1]]

        inputs = processor(
            images=np.array(raw_image), input_points=input_points, input_labels=input_labels, return_tensors="pt"
        ).to(device)

        with torch.no_grad():
            output = hf_model(**inputs)
        scores = output.iou_scores.squeeze()

        assert scores[-1].item() == 0.9936047792434692

    if pytorch_dump_folder is not None:
        processor.save_pretrained(pytorch_dump_folder)
        hf_model.save_pretrained(pytorch_dump_folder)

    if push_to_hub:
        repo_id = f"nielsr/{model_name}" if "slimsam" in model_name else f"meta/{model_name}"
        processor.push_to_hub(repo_id)
        hf_model.push_to_hub(repo_id)