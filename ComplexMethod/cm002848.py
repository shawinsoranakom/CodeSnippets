def convert_d_fine_checkpoint(model_name, pytorch_dump_folder_path, push_to_hub, repo_id):
    """
    Copy/paste/tweak model's weights to our D-FINE structure.
    """

    # load default config
    config = get_d_fine_config(model_name)
    state_dict = load_original_state_dict(repo_id, model_name)
    state_dict.pop("decoder.valid_mask", None)
    state_dict.pop("decoder.anchors", None)
    model = DFineForObjectDetection(config)
    logger.info(f"Converting model {model_name}...")

    state_dict = convert_old_keys_to_new_keys(state_dict)
    state_dict.pop("decoder.model.decoder.up", None)
    state_dict.pop("decoder.model.decoder.reg_scale", None)

    # query, key and value matrices need special treatment
    read_in_q_k_v(state_dict, config, model_name)
    # important: we need to prepend a prefix to each of the base model keys as the head models use different attributes for them
    for key in state_dict.copy():
        if key.endswith("num_batches_tracked"):
            del state_dict[key]
        # for two_stage
        if "bbox_embed" in key or ("class_embed" in key and "denoising_" not in key):
            state_dict[key.split("model.decoder.")[-1]] = state_dict[key]

    # finally, create HuggingFace model and load state dict
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

    outputs = model(pixel_values)

    if model_name == "dfine_x_coco":
        expected_slice_logits = torch.tensor(
            [
                [-4.844723, -4.7293096, -4.5971327],
                [-4.554266, -4.61723, -4.627926],
                [-4.3934402, -4.6064143, -4.139952],
            ]
        )
        expected_slice_boxes = torch.tensor(
            [
                [0.2565248, 0.5477609, 0.47644863],
                [0.7690029, 0.41423926, 0.46148556],
                [0.1688096, 0.19923759, 0.21118002],
            ]
        )
    elif model_name == "dfine_x_obj2coco":
        expected_slice_logits = torch.tensor(
            [
                [-4.230433, -6.6295037, -4.8339615],
                [-4.085411, -6.3280816, -4.695468],
                [-3.8968022, -6.336813, -4.67051],
            ]
        )
        expected_slice_boxes = torch.tensor(
            [
                [0.25707328, 0.54842496, 0.47624254],
                [0.76967394, 0.41272867, 0.45970756],
                [0.16882066, 0.19918433, 0.2112098],
            ]
        )
    elif model_name == "dfine_x_obj365":
        expected_slice_logits = torch.tensor(
            [
                [-6.3844957, -3.7549126, -4.6873264],
                [-5.8433194, -3.4490552, -3.3228905],
                [-6.5314736, -3.7856622, -4.895984],
            ]
        )
        expected_slice_boxes = torch.tensor(
            [
                [0.7703046, 0.41329497, 0.45932162],
                [0.16898105, 0.19876392, 0.21050783],
                [0.25134972, 0.5517619, 0.4864124],
            ]
        )
    elif model_name == "dfine_m_coco":
        expected_slice_logits = torch.tensor(
            [
                [-4.5187078, -4.71708, -4.117749],
                [-4.513984, -4.937715, -3.829125],
                [-4.830042, -6.931682, -3.1740026],
            ]
        )
        expected_slice_boxes = torch.tensor(
            [
                [0.25851426, 0.5489963, 0.4757598],
                [0.769683, 0.41411665, 0.45988125],
                [0.16866133, 0.19921188, 0.21207744],
            ]
        )
    elif model_name == "dfine_m_obj2coco":
        expected_slice_logits = torch.tensor(
            [
                [-4.520666, -7.6678333, -5.739887],
                [-4.5053635, -7.510611, -5.452532],
                [-4.70348, -5.6098466, -5.0199957],
            ]
        )
        expected_slice_boxes = torch.tensor(
            [
                [0.2567608, 0.5485795, 0.4767465],
                [0.77035284, 0.41236404, 0.4580645],
                [0.5498525, 0.27548885, 0.05886984],
            ]
        )
    elif model_name == "dfine_m_obj365":
        expected_slice_logits = torch.tensor(
            [
                [-5.770525, -3.1610885, -5.2807794],
                [-5.7809954, -3.768266, -5.1146393],
                [-6.180705, -3.7357295, -3.1651964],
            ]
        )
        expected_slice_boxes = torch.tensor(
            [
                [0.2529114, 0.5526663, 0.48270613],
                [0.7712474, 0.41294736, 0.457174],
                [0.5497157, 0.27588123, 0.05813372],
            ]
        )
    elif model_name == "dfine_l_coco":
        expected_slice_logits = torch.tensor(
            [
                [-4.068779, -5.169955, -4.339212],
                [-3.9461594, -5.0279613, -4.0161457],
                [-4.218292, -6.196324, -5.175245],
            ]
        )
        expected_slice_boxes = torch.tensor(
            [
                [0.2564867, 0.5489948, 0.4748876],
                [0.7693534, 0.4138953, 0.4598034],
                [0.16875696, 0.19875404, 0.21196914],
            ]
        )
    elif model_name == "dfine_l_obj365":
        expected_slice_logits = torch.tensor(
            [
                [-5.7953215, -3.4901116, -5.4394145],
                [-5.7032104, -3.671125, -5.76121],
                [-6.09466, -3.1512096, -4.285499],
            ]
        )
        expected_slice_boxes = torch.tensor(
            [
                [0.7693825, 0.41265628, 0.4606362],
                [0.25306237, 0.55187637, 0.4832178],
                [0.16892478, 0.19880727, 0.21115331],
            ]
        )
    elif model_name == "dfine_l_obj2coco_e25":
        expected_slice_logits = torch.tensor(
            [
                [-3.6098495, -6.633563, -5.1227236],
                [-3.682696, -6.9178205, -5.414557],
                [-4.491674, -6.0823426, -4.5718226],
            ]
        )
        expected_slice_boxes = torch.tensor(
            [
                [0.7697078, 0.41368833, 0.45879585],
                [0.2573691, 0.54856044, 0.47715297],
                [0.16895264, 0.19871138, 0.2115552],
            ]
        )
    elif model_name == "dfine_n_coco":
        expected_slice_logits = torch.tensor(
            [
                [-3.7827945, -5.0889463, -4.8341026],
                [-5.3046904, -6.2801714, -2.9276395],
                [-4.497901, -5.2670407, -6.2380104],
            ]
        )
        expected_slice_boxes = torch.tensor(
            [
                [0.73334837, 0.4270624, 0.39424777],
                [0.1680235, 0.1988639, 0.21031213],
                [0.25370035, 0.5534435, 0.48496848],
            ]
        )
    elif model_name == "dfine_s_coco":
        expected_slice_logits = torch.tensor(
            [
                [-3.8097816, -4.7724586, -5.994499],
                [-5.2974715, -9.499067, -6.1653666],
                [-5.3502765, -3.9530406, -6.3630295],
            ]
        )
        expected_slice_boxes = torch.tensor(
            [
                [0.7677696, 0.41479152, 0.46441072],
                [0.16912134, 0.19869131, 0.2123824],
                [0.2581653, 0.54818195, 0.47512347],
            ]
        )
    elif model_name == "dfine_s_obj2coco":
        expected_slice_logits = torch.tensor(
            [
                [-6.0208125, -7.532673, -5.0572147],
                [-3.3595953, -9.057545, -6.376975],
                [-4.3203554, -9.546032, -6.075504],
            ]
        )
        expected_slice_boxes = torch.tensor(
            [
                [0.16901012, 0.19883151, 0.21121952],
                [0.76784194, 0.41266578, 0.46402973],
                [00.2563128, 0.54797643, 0.47937632],
            ]
        )
    elif model_name == "dfine_s_obj365":
        expected_slice_logits = torch.tensor(
            [
                [-6.3807316, -4.320986, -6.4775343],
                [-6.5818424, -3.5009093, -5.75824],
                [-5.748005, -4.3228016, -4.003726],
            ]
        )
        expected_slice_boxes = torch.tensor(
            [
                [0.2532072, 0.5491191, 0.48222217],
                [0.76586807, 0.41175705, 0.46789962],
                [0.169111, 0.19844547, 0.21069047],
            ]
        )
    else:
        raise ValueError(f"Unknown d_fine_name: {model_name}")

    assert torch.allclose(outputs.logits[0, :3, :3], expected_slice_logits.to(outputs.logits.device), atol=1e-3)
    assert torch.allclose(outputs.pred_boxes[0, :3, :3], expected_slice_boxes.to(outputs.pred_boxes.device), atol=1e-4)

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
            repo_id=repo_id,
            commit_message="Add config from convert_d_fine_original_pytorch_checkpoint_to_hf.py",
        )
        model.push_to_hub(
            repo_id=repo_id,
            commit_message="Add model from convert_d_fine_original_pytorch_checkpoint_to_hf.py",
        )
        image_processor.push_to_hub(
            repo_id=repo_id,
            commit_message="Add image processor from convert_d_fine_original_pytorch_checkpoint_to_hf.py",
        )