def convert_table_transformer_checkpoint(checkpoint_url, pytorch_dump_folder_path, push_to_hub):
    """
    Copy/paste/tweak model's weights to our DETR structure.
    """

    logger.info("Converting model...")

    # load original state dict
    state_dict = torch.hub.load_state_dict_from_url(checkpoint_url, map_location="cpu")
    # rename keys
    for src, dest in rename_keys:
        rename_key(state_dict, src, dest)
    state_dict = rename_backbone_keys(state_dict)
    # query, key and value matrices need special treatment
    read_in_q_k_v(state_dict)
    # important: we need to prepend a prefix to each of the base model keys as the head models use different attributes for them
    prefix = "model."
    for key in state_dict.copy():
        if not key.startswith("class_labels_classifier") and not key.startswith("bbox_predictor"):
            val = state_dict.pop(key)
            state_dict[prefix + key] = val
    # create HuggingFace model and load state dict
    config = TableTransformerConfig(
        backbone="resnet18",
        mask_loss_coefficient=1,
        dice_loss_coefficient=1,
        ce_loss_coefficient=1,
        bbox_loss_coefficient=5,
        giou_loss_coefficient=2,
        eos_coefficient=0.4,
        class_cost=1,
        bbox_cost=5,
        giou_cost=2,
    )

    if "detection" in checkpoint_url:
        config.num_queries = 15
        config.num_labels = 2
        id2label = {0: "table", 1: "table rotated"}
        config.id2label = id2label
        config.label2id = {v: k for k, v in id2label.items()}
    else:
        config.num_queries = 125
        config.num_labels = 6
        id2label = {
            0: "table",
            1: "table column",
            2: "table row",
            3: "table column header",
            4: "table projected row header",
            5: "table spanning cell",
        }
        config.id2label = id2label
        config.label2id = {v: k for k, v in id2label.items()}

    image_processor = DetrImageProcessor(
        format="coco_detection", max_size=800 if "detection" in checkpoint_url else 1000
    )
    model = TableTransformerForObjectDetection(config)
    model.load_state_dict(state_dict)
    model.eval()

    # verify our conversion
    filename = "example_pdf.png" if "detection" in checkpoint_url else "example_table.png"
    file_path = hf_hub_download(repo_id="nielsr/example-pdf", repo_type="dataset", filename=filename)
    image = Image.open(file_path).convert("RGB")
    pixel_values = normalize(resize(image, checkpoint_url)).unsqueeze(0)

    outputs = model(pixel_values)

    if "detection" in checkpoint_url:
        expected_shape = (1, 15, 3)
        expected_logits = torch.tensor(
            [[-6.7897, -16.9985, 6.7937], [-8.0186, -22.2192, 6.9677], [-7.3117, -21.0708, 7.4055]]
        )
        expected_boxes = torch.tensor([[0.4867, 0.1767, 0.6732], [0.6718, 0.4479, 0.3830], [0.4716, 0.1760, 0.6364]])

    else:
        expected_shape = (1, 125, 7)
        expected_logits = torch.tensor(
            [[-18.1430, -8.3214, 4.8274], [-18.4685, -7.1361, -4.2667], [-26.3693, -9.3429, -4.9962]]
        )
        expected_boxes = torch.tensor([[0.4983, 0.5595, 0.9440], [0.4916, 0.6315, 0.5954], [0.6108, 0.8637, 0.1135]])

    assert outputs.logits.shape == expected_shape
    assert torch.allclose(outputs.logits[0, :3, :3], expected_logits, atol=1e-4)
    assert torch.allclose(outputs.pred_boxes[0, :3, :3], expected_boxes, atol=1e-4)
    print("Looks ok!")

    if pytorch_dump_folder_path is not None:
        # Save model and image processor
        logger.info(f"Saving PyTorch model and image processor to {pytorch_dump_folder_path}...")
        Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
        model.save_pretrained(pytorch_dump_folder_path)
        image_processor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        # Push model to HF hub
        logger.info("Pushing model to the hub...")
        model_name = (
            "microsoft/table-transformer-detection"
            if "detection" in checkpoint_url
            else "microsoft/table-transformer-structure-recognition"
        )
        model.push_to_hub(model_name)
        image_processor.push_to_hub(model_name)