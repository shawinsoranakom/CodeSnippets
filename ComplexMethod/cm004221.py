def convert_detr_checkpoint(model_name, pytorch_dump_folder_path):
    """
    Copy/paste/tweak model's weights to our DETR structure.
    """

    # load default config
    config = DetrConfig()
    # set backbone and dilation attributes
    if "resnet101" in model_name:
        config.backbone = "resnet101"
    if "dc5" in model_name:
        config.dilation = True
    is_panoptic = "panoptic" in model_name
    if is_panoptic:
        config.num_labels = 250
    else:
        config.num_labels = 91
        repo_id = "huggingface/label-files"
        filename = "coco-detection-id2label.json"
        id2label = json.load(open(hf_hub_download(repo_id, filename, repo_type="dataset"), "r"))
        id2label = {int(k): v for k, v in id2label.items()}
        config.id2label = id2label
        config.label2id = {v: k for k, v in id2label.items()}

    # load image processor
    format = "coco_panoptic" if is_panoptic else "coco_detection"
    image_processor = DetrImageProcessor(format=format)

    # prepare image
    img = prepare_img()
    encoding = image_processor(images=img, return_tensors="pt")
    pixel_values = encoding["pixel_values"]

    logger.info(f"Converting model {model_name}...")

    # load original model from torch hub
    detr = torch.hub.load("facebookresearch/detr", model_name, pretrained=True).eval()
    state_dict = detr.state_dict()
    # rename keys
    for src, dest in rename_keys:
        if is_panoptic:
            src = "detr." + src
        rename_key(state_dict, src, dest)
    state_dict = rename_backbone_keys(state_dict)
    # query, key and value matrices need special treatment
    read_in_q_k_v(state_dict, is_panoptic=is_panoptic)
    # important: we need to prepend a prefix to each of the base model keys as the head models use different attributes for them
    prefix = "detr.model." if is_panoptic else "model."
    for key in state_dict.copy():
        if is_panoptic:
            if (
                key.startswith("detr")
                and not key.startswith("class_labels_classifier")
                and not key.startswith("bbox_predictor")
            ):
                val = state_dict.pop(key)
                state_dict["detr.model" + key[4:]] = val
            elif "class_labels_classifier" in key or "bbox_predictor" in key:
                val = state_dict.pop(key)
                state_dict["detr." + key] = val
            elif key.startswith("bbox_attention") or key.startswith("mask_head"):
                continue
            else:
                val = state_dict.pop(key)
                state_dict[prefix + key] = val
        else:
            if not key.startswith("class_labels_classifier") and not key.startswith("bbox_predictor"):
                val = state_dict.pop(key)
                state_dict[prefix + key] = val
    # finally, create HuggingFace model and load state dict
    model = DetrForSegmentation(config) if is_panoptic else DetrForObjectDetection(config)
    model.load_state_dict(state_dict)
    model.eval()
    # verify our conversion
    original_outputs = detr(pixel_values)
    outputs = model(pixel_values)
    assert torch.allclose(outputs.logits, original_outputs["pred_logits"], atol=1e-4)
    assert torch.allclose(outputs.pred_boxes, original_outputs["pred_boxes"], atol=1e-4)
    if is_panoptic:
        assert torch.allclose(outputs.pred_masks, original_outputs["pred_masks"], atol=1e-4)

    # Save model and image processor
    logger.info(f"Saving PyTorch model and image processor to {pytorch_dump_folder_path}...")
    Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
    model.save_pretrained(pytorch_dump_folder_path)
    image_processor.save_pretrained(pytorch_dump_folder_path)