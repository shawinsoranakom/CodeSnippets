def convert_and_test_dinov3_checkpoint(args):
    expected_outputs = {
        "vits16_lvd1689m_cls": [0.463561, -0.415609, 0.408236, -0.126613, -0.286636],
        "vits16_lvd1689m_patch": [-0.038754, -0.250895, -0.016392, -0.455473, 0.571582],
        "vits16plus_lvd1689m_cls": [-0.471349, -1.365778, -0.317983, 0.377219, -0.769085],
        "vits16plus_lvd1689m_patch": [0.144551, -0.388117, -0.393433, -0.157695, -0.600380],
        "vitb16_lvd1689m_cls": [1.034643, -0.180609, -0.341018, -0.066376, -0.011383],
        "vitb16_lvd1689m_patch": [-0.082523, -0.456272, -0.728029, -0.430680, -0.152880],
        "vitl16_lvd1689m_cls": [0.484527, -0.582214, 0.480636, 0.592040, 0.945166],
        "vitl16_lvd1689m_patch": [-0.211367, -0.490863, -0.257131, 0.101763, 0.154511],
        "vith16plus_lvd1689m_cls": [-0.064575, -0.148866, -0.621524, 0.634878, 0.152695],
        "vith16plus_lvd1689m_patch": [-0.093817, 0.287407, -0.050036, 0.428043, 0.094561],
        "vit7b16_lvd1689m_cls": [0.275439, -0.261353, 0.067772, 0.049936, -0.158747],
        "vit7b16_lvd1689m_patch": [0.044442, -0.052542, 0.070777, -0.065111, -0.026546],
        "vitl16_sat493m_cls": [-0.33235, 0.34052, -0.22087, 0.21434, 0.09003],
        "vitl16_sat493m_patch": [0.18488, 0.30309, -0.20689, 0.12848, 0.06207],
        "vit7b16_sat493m_cls": [-0.19779, 0.11819, -0.00581, -0.21055, -0.03971],
        "vit7b16_sat493m_patch": [-0.12423, 0.07879, -0.10057, 0.02835, -0.11727],
    }

    model_name = args.model_name
    config = get_dinov3_config(model_name)

    model = DINOv3ViTModel(config).eval()
    state_dict_path = hf_hub_download(repo_id=HUB_MODELS[model_name], filename=HUB_CHECKPOINTS[model_name])
    original_state_dict = torch.load(state_dict_path, mmap=True)

    original_state_dict = split_qkv(original_state_dict)
    original_keys = list(original_state_dict.keys())
    new_keys = convert_old_keys_to_new_keys(original_keys)

    converted_state_dict = {}
    for key in original_keys:
        new_key = new_keys[key]
        weight_tensor = original_state_dict[key]

        if "bias_mask" in key or "attn.k_proj.bias" in key or "local_cls_norm" in key:
            continue
        if "embeddings.mask_token" in new_key:
            weight_tensor = weight_tensor.unsqueeze(1)
        if "inv_freq" in new_key:
            continue

        converted_state_dict[new_key] = weight_tensor

    model.load_state_dict(converted_state_dict, strict=True)
    model = model.eval()

    transform = get_transform()
    image_processor = get_image_processor()
    image = prepare_img()

    # check preprocessing
    original_pixel_values = transform(image).unsqueeze(0)  # add batch dimension
    inputs = image_processor(image, return_tensors="pt")

    torch.testing.assert_close(original_pixel_values, inputs["pixel_values"], atol=1e-6, rtol=1e-6)
    print("Preprocessing looks ok!")

    with torch.inference_mode(), torch.autocast("cuda", dtype=torch.float):
        model_output = model(**inputs)

    last_layer_class_token = model_output.pooler_output
    last_layer_patch_tokens = model_output.last_hidden_state[:, config.num_register_tokens + 1 :]

    actual_outputs = {}
    actual_outputs[f"{model_name}_cls"] = last_layer_class_token[0, :5].tolist()
    actual_outputs[f"{model_name}_patch"] = last_layer_patch_tokens[0, 0, :5].tolist()

    print("Actual:  ", [round(x, 6) for x in actual_outputs[f"{model_name}_cls"]])
    print("Expected:", expected_outputs[f"{model_name}_cls"])

    torch.testing.assert_close(
        torch.Tensor(actual_outputs[f"{model_name}_cls"]),
        torch.Tensor(expected_outputs[f"{model_name}_cls"]),
        atol=1e-3,
        rtol=1e-3,
    )
    torch.testing.assert_close(
        torch.Tensor(actual_outputs[f"{model_name}_patch"]),
        torch.Tensor(expected_outputs[f"{model_name}_patch"]),
        atol=1e-3,
        rtol=1e-3,
    )
    print("Forward pass looks ok!")

    save_dir = os.path.join(args.save_dir, model_name)
    os.makedirs(save_dir, exist_ok=True)
    model.save_pretrained(save_dir)
    image_processor.save_pretrained(save_dir)
    print(f"Model saved to {save_dir}")

    if args.push_to_hub:
        api = HfApi()
        repo = HUB_MODELS[model_name]
        api.upload_folder(folder_path=save_dir, repo_id=repo, repo_type="model")