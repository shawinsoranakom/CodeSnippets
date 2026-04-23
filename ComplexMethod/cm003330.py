def convert_rt_detr_checkpoint(model_name, pytorch_dump_folder_path, push_to_hub, repo_id):
    """
    Copy/paste/tweak model's weights to our RTDETR structure.
    """

    # load default config
    config = get_rt_detr_config(model_name)

    # load original model from torch hub
    model_name_to_checkpoint_url = {
        "rtdetr_r18vd": "https://github.com/lyuwenyu/storage/releases/download/v0.1/rtdetr_r18vd_dec3_6x_coco_from_paddle.pth",
        "rtdetr_r34vd": "https://github.com/lyuwenyu/storage/releases/download/v0.1/rtdetr_r34vd_dec4_6x_coco_from_paddle.pth",
        "rtdetr_r50vd_m": "https://github.com/lyuwenyu/storage/releases/download/v0.1/rtdetr_r50vd_m_6x_coco_from_paddle.pth",
        "rtdetr_r50vd": "https://github.com/lyuwenyu/storage/releases/download/v0.1/rtdetr_r50vd_6x_coco_from_paddle.pth",
        "rtdetr_r101vd": "https://github.com/lyuwenyu/storage/releases/download/v0.1/rtdetr_r101vd_6x_coco_from_paddle.pth",
        "rtdetr_r18vd_coco_o365": "https://github.com/lyuwenyu/storage/releases/download/v0.1/rtdetr_r18vd_5x_coco_objects365_from_paddle.pth",
        "rtdetr_r50vd_coco_o365": "https://github.com/lyuwenyu/storage/releases/download/v0.1/rtdetr_r50vd_2x_coco_objects365_from_paddle.pth",
        "rtdetr_r101vd_coco_o365": "https://github.com/lyuwenyu/storage/releases/download/v0.1/rtdetr_r101vd_2x_coco_objects365_from_paddle.pth",
    }
    logger.info(f"Converting model {model_name}...")
    state_dict = torch.hub.load_state_dict_from_url(model_name_to_checkpoint_url[model_name], map_location="cpu")[
        "ema"
    ]["module"]

    # rename keys
    for src, dest in create_rename_keys(config):
        rename_key(state_dict, src, dest)
    # query, key and value matrices need special treatment
    read_in_q_k_v(state_dict, config)
    # important: we need to prepend a prefix to each of the base model keys as the head models use different attributes for them
    for key in state_dict.copy():
        if key.endswith("num_batches_tracked"):
            del state_dict[key]
        # for two_stage
        if "bbox_embed" in key or ("class_embed" in key and "denoising_" not in key):
            state_dict[key.split("model.decoder.")[-1]] = state_dict[key]

    # finally, create HuggingFace model and load state dict
    model = RTDetrForObjectDetection(config)
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
    outputs = model(pixel_values)

    if model_name == "rtdetr_r18vd":
        expected_slice_logits = torch.tensor(
            [
                [-4.3364253, -6.465683, -3.6130402],
                [-4.083815, -6.4039373, -6.97881],
                [-4.192215, -7.3410473, -6.9027247],
            ]
        )
        expected_slice_boxes = torch.tensor(
            [
                [0.16868353, 0.19833282, 0.21182671],
                [0.25559652, 0.55121744, 0.47988364],
                [0.7698693, 0.4124569, 0.46036878],
            ]
        )
    elif model_name == "rtdetr_r34vd":
        expected_slice_logits = torch.tensor(
            [
                [-4.3727384, -4.7921476, -5.7299604],
                [-4.840536, -8.455345, -4.1745796],
                [-4.1277084, -5.2154565, -5.7852697],
            ]
        )
        expected_slice_boxes = torch.tensor(
            [
                [0.258278, 0.5497808, 0.4732004],
                [0.16889669, 0.19890057, 0.21138911],
                [0.76632994, 0.4147879, 0.46851268],
            ]
        )
    elif model_name == "rtdetr_r50vd_m":
        expected_slice_logits = torch.tensor(
            [
                [-4.319764, -6.1349025, -6.094794],
                [-5.1056995, -7.744766, -4.803956],
                [-4.7685347, -7.9278393, -4.5751696],
            ]
        )
        expected_slice_boxes = torch.tensor(
            [
                [0.2582739, 0.55071366, 0.47660282],
                [0.16811174, 0.19954777, 0.21292639],
                [0.54986024, 0.2752091, 0.0561416],
            ]
        )
    elif model_name == "rtdetr_r50vd":
        expected_slice_logits = torch.tensor(
            [
                [-4.6476398, -5.001154, -4.9785104],
                [-4.1593494, -4.7038546, -5.946485],
                [-4.4374595, -4.658361, -6.2352347],
            ]
        )
        expected_slice_boxes = torch.tensor(
            [
                [0.16880608, 0.19992264, 0.21225442],
                [0.76837635, 0.4122631, 0.46368608],
                [0.2595386, 0.5483334, 0.4777486],
            ]
        )
    elif model_name == "rtdetr_r101vd":
        expected_slice_logits = torch.tensor(
            [
                [-4.6162, -4.9189, -4.6656],
                [-4.4701, -4.4997, -4.9659],
                [-5.6641, -7.9000, -5.0725],
            ]
        )
        expected_slice_boxes = torch.tensor(
            [
                [0.7707, 0.4124, 0.4585],
                [0.2589, 0.5492, 0.4735],
                [0.1688, 0.1993, 0.2108],
            ]
        )
    elif model_name == "rtdetr_r18vd_coco_o365":
        expected_slice_logits = torch.tensor(
            [
                [-4.8726, -5.9066, -5.2450],
                [-4.8157, -6.8764, -5.1656],
                [-4.7492, -5.7006, -5.1333],
            ]
        )
        expected_slice_boxes = torch.tensor(
            [
                [0.2552, 0.5501, 0.4773],
                [0.1685, 0.1986, 0.2104],
                [0.7692, 0.4141, 0.4620],
            ]
        )
    elif model_name == "rtdetr_r50vd_coco_o365":
        expected_slice_logits = torch.tensor(
            [
                [-4.6491, -3.9252, -5.3163],
                [-4.1386, -5.0348, -3.9016],
                [-4.4778, -4.5423, -5.7356],
            ]
        )
        expected_slice_boxes = torch.tensor(
            [
                [0.2583, 0.5492, 0.4747],
                [0.5501, 0.2754, 0.0574],
                [0.7693, 0.4137, 0.4613],
            ]
        )
    elif model_name == "rtdetr_r101vd_coco_o365":
        expected_slice_logits = torch.tensor(
            [
                [-4.5152, -5.6811, -5.7311],
                [-4.5358, -7.2422, -5.0941],
                [-4.6919, -5.5834, -6.0145],
            ]
        )
        expected_slice_boxes = torch.tensor(
            [
                [0.7703, 0.4140, 0.4583],
                [0.1686, 0.1991, 0.2107],
                [0.2570, 0.5496, 0.4750],
            ]
        )
    else:
        raise ValueError(f"Unknown rt_detr_name: {model_name}")

    assert torch.allclose(outputs.logits[0, :3, :3], expected_slice_logits.to(outputs.logits.device), atol=1e-4)
    assert torch.allclose(outputs.pred_boxes[0, :3, :3], expected_slice_boxes.to(outputs.pred_boxes.device), atol=1e-3)

    if pytorch_dump_folder_path is not None:
        Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
        print(f"Saving model {model_name} to {pytorch_dump_folder_path}")
        model.save_pretrained(pytorch_dump_folder_path)
        print(f"Saving image processor to {pytorch_dump_folder_path}")
        image_processor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        # Upload model, image processor and config to the hub
        logger.info("Uploading PyTorch model and image processor to the hub...")
        config.push_to_hub(
            repo_id=repo_id, commit_message="Add config from convert_rt_detr_original_pytorch_checkpoint_to_pytorch.py"
        )
        model.push_to_hub(
            repo_id=repo_id, commit_message="Add model from convert_rt_detr_original_pytorch_checkpoint_to_pytorch.py"
        )
        image_processor.push_to_hub(
            repo_id=repo_id,
            commit_message="Add image processor from convert_rt_detr_original_pytorch_checkpoint_to_pytorch.py",
        )