def write_model_and_image_processor(model_name, output_dir, push_to_hub, repo_id):
    """
    Copy/paste/tweak model's weights to our RTDETR structure.
    """

    # load default config
    config = get_rt_detr_v2_config(model_name)

    # load original model from torch hub
    model_name_to_checkpoint_url = {
        "rtdetr_v2_r18vd": "https://github.com/lyuwenyu/storage/releases/download/v0.2/rtdetrv2_r18vd_120e_coco_rerun_48.1.pth",
        "rtdetr_v2_r34vd": "https://github.com/lyuwenyu/storage/releases/download/v0.1/rtdetrv2_r34vd_120e_coco_ema.pth",
        "rtdetr_v2_r50vd": "https://github.com/lyuwenyu/storage/releases/download/v0.1/rtdetrv2_r50vd_6x_coco_ema.pth",
        "rtdetr_v2_r101vd": "https://github.com/lyuwenyu/storage/releases/download/v0.1/rtdetrv2_r101vd_6x_coco_from_paddle.pth",
    }
    logger.info(f"Converting model {model_name}...")
    state_dict = torch.hub.load_state_dict_from_url(model_name_to_checkpoint_url[model_name], map_location="cpu")[
        "ema"
    ]["module"]
    # rename keys
    state_dict = convert_old_keys_to_new_keys(state_dict)
    for key in state_dict.copy():
        if key.endswith("num_batches_tracked"):
            del state_dict[key]
    # query, key and value matrices need special treatment
    read_in_q_k_v(state_dict, config)
    # important: we need to prepend a prefix to each of the base model keys as the head models use different attributes for them
    for key in state_dict.copy():
        if key.endswith("num_batches_tracked"):
            del state_dict[key]
        # for two_stage
        if "bbox_embed" in key or ("class_embed" in key and "denoising_" not in key):
            state_dict[key.split("model.decoder.")[-1]] = state_dict[key]

    # no need in ckpt
    del state_dict["decoder.anchors"]
    del state_dict["decoder.valid_mask"]
    # finally, create HuggingFace model and load state dict
    model = RTDetrV2ForObjectDetection(config)
    model.load_state_dict(state_dict)
    model.eval()

    # load image processor
    image_processor = RTDetrImageProcessor()

    # prepare image
    img = prepare_img()

    # preprocess image
    transformations = transforms.Compose(
        [
            transforms.Resize([640, 640], interpolation=transforms.InterpolationMode.BILINEAR),
            transforms.ToTensor(),
        ]
    )
    original_pixel_values = transformations(img).unsqueeze(0)  # insert batch dimension

    encoding = image_processor(images=img, return_tensors="pt")
    pixel_values = encoding["pixel_values"]

    assert torch.allclose(original_pixel_values, pixel_values)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    pixel_values = pixel_values.to(device)

    # Pass image by the model
    with torch.no_grad():
        outputs = model(pixel_values)

    if model_name == "rtdetr_v2_r18vd":
        expected_slice_logits = torch.tensor(
            [[-3.7045, -5.1913, -6.1787], [-4.0106, -9.3450, -5.2043], [-4.1287, -4.7463, -5.8634]]
        )
        expected_slice_boxes = torch.tensor(
            [[0.2582, 0.5497, 0.4764], [0.1684, 0.1985, 0.2120], [0.7665, 0.4146, 0.4669]]
        )
    elif model_name == "rtdetr_v2_r34vd":
        expected_slice_logits = torch.tensor(
            [[-4.6108, -5.9453, -3.8505], [-3.8702, -6.1136, -5.5677], [-3.7790, -6.4538, -5.9449]]
        )
        expected_slice_boxes = torch.tensor(
            [[0.1691, 0.1984, 0.2118], [0.2594, 0.5506, 0.4736], [0.7669, 0.4136, 0.4654]]
        )
    elif model_name == "rtdetr_v2_r50vd":
        expected_slice_logits = torch.tensor(
            [[-4.7881, -4.6754, -6.1624], [-5.4441, -6.6486, -4.3840], [-3.5455, -4.9318, -6.3544]]
        )
        expected_slice_boxes = torch.tensor(
            [[0.2588, 0.5487, 0.4747], [0.5497, 0.2760, 0.0573], [0.7688, 0.4133, 0.4634]]
        )
    elif model_name == "rtdetr_v2_r101vd":
        expected_slice_logits = torch.tensor(
            [[-4.6162, -4.9189, -4.6656], [-4.4701, -4.4997, -4.9659], [-5.6641, -7.9000, -5.0725]]
        )
        expected_slice_boxes = torch.tensor(
            [[0.7707, 0.4124, 0.4585], [0.2589, 0.5492, 0.4735], [0.1688, 0.1993, 0.2108]]
        )
    else:
        raise ValueError(f"Unknown rt_detr_v2_name: {model_name}")
    assert torch.allclose(outputs.logits[0, :3, :3], expected_slice_logits.to(outputs.logits.device), atol=1e-4)
    assert torch.allclose(outputs.pred_boxes[0, :3, :3], expected_slice_boxes.to(outputs.pred_boxes.device), atol=1e-3)

    if output_dir is not None:
        Path(output_dir).mkdir(exist_ok=True)
        print(f"Saving model {model_name} to {output_dir}")
        model.save_pretrained(output_dir)
        print(f"Saving image processor to {output_dir}")
        image_processor.save_pretrained(output_dir)

    if push_to_hub:
        # Upload model, image processor and config to the hub
        logger.info("Uploading PyTorch model and image processor to the hub...")
        config.push_to_hub(
            repo_id=repo_id,
            commit_message="Add config from convert_rt_detr_v2_original_pytorch_checkpoint_to_pytorch.py",
        )
        model.push_to_hub(
            repo_id=repo_id,
            commit_message="Add model from convert_rt_detr_v2_original_pytorch_checkpoint_to_pytorch.py",
        )
        image_processor.push_to_hub(
            repo_id=repo_id,
            commit_message="Add image processor from convert_rt_detr_v2_original_pytorch_checkpoint_to_pytorch.py",
        )