def convert_textnet_checkpoint(checkpoint_url, checkpoint_config_filename, pytorch_dump_folder_path):
    config_filepath = hf_hub_download(repo_id="Raghavan/fast_model_config_files", filename="fast_model_configs.json")

    with open(config_filepath) as f:
        content = json.loads(f.read())

    size = content[checkpoint_config_filename]["short_size"]

    if "tiny" in content[checkpoint_config_filename]["config"]:
        config = prepare_config(tiny_config_url, size)
        expected_slice_backbone = torch.tensor(
            [0.0000, 0.0000, 0.0000, 0.0000, 0.5300, 0.0000, 0.0000, 0.0000, 0.0000, 1.1221]
        )
    elif "small" in content[checkpoint_config_filename]["config"]:
        config = prepare_config(small_config_url, size)
        expected_slice_backbone = torch.tensor(
            [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.1394]
        )
    else:
        config = prepare_config(base_config_url, size)
        expected_slice_backbone = torch.tensor(
            [0.9210, 0.6099, 0.0000, 0.0000, 0.0000, 0.0000, 3.2207, 2.6602, 1.8925, 0.0000]
        )

    model = TextNetBackbone(config)
    textnet_image_processor = TextNetImageProcessor(size={"shortest_edge": size})
    state_dict = torch.hub.load_state_dict_from_url(checkpoint_url, map_location="cpu", check_hash=True)["ema"]
    state_dict_changed = OrderedDict()
    for key in state_dict:
        if "backbone" in key:
            val = state_dict[key]
            new_key = key
            for search, replacement in rename_key_mappings.items():
                if search in new_key:
                    new_key = new_key.replace(search, replacement)

            pattern = r"textnet\.stage(\d)"

            def adjust_stage(match):
                stage_number = int(match.group(1)) - 1
                return f"textnet.encoder.stages.{stage_number}.stage"

            # Using regex to find and replace the pattern in the string
            new_key = re.sub(pattern, adjust_stage, new_key)
            state_dict_changed[new_key] = val
    model.load_state_dict(state_dict_changed)
    model.eval()

    url = "http://images.cocodataset.org/val2017/000000039769.jpg"
    with httpx.stream("GET", url) as response:
        image = Image.open(BytesIO(response.read())).convert("RGB")

    original_pixel_values = torch.tensor(
        [0.1939, 0.3481, 0.4166, 0.3309, 0.4508, 0.4679, 0.4851, 0.4851, 0.3309, 0.4337]
    )
    pixel_values = textnet_image_processor(image, return_tensors="pt").pixel_values

    assert torch.allclose(original_pixel_values, pixel_values[0][0][3][:10], atol=1e-4)

    with torch.no_grad():
        output = model(pixel_values)

    assert torch.allclose(output["feature_maps"][-1][0][10][12][:10].detach(), expected_slice_backbone, atol=1e-3)

    model.save_pretrained(pytorch_dump_folder_path)
    textnet_image_processor.save_pretrained(pytorch_dump_folder_path)
    logging.info("The converted weights are saved here : " + pytorch_dump_folder_path)