def convert_vitmatte_checkpoint(model_name, pytorch_dump_folder_path, push_to_hub):
    config = get_config(model_name)

    # load original state dict
    model_name_to_filename = {
        "vitmatte-small-composition-1k": "ViTMatte_S_Com.pth",
        "vitmatte-base-composition-1k": "ViTMatte_B_Com.pth",
        "vitmatte-small-distinctions-646": "ViTMatte_S_DIS.pth",
        "vitmatte-base-distinctions-646": "ViTMatte_B_DIS.pth",
    }

    filename = model_name_to_filename[model_name]
    filepath = hf_hub_download(repo_id="nielsr/vitmatte-checkpoints", filename=filename, repo_type="model")
    state_dict = torch.load(filepath, map_location="cpu", weights_only=True)

    # rename keys
    for key in state_dict.copy():
        val = state_dict.pop(key)
        if "backbone.blocks" in key:
            key = key.replace("backbone.blocks", "backbone.encoder.layer")
        if "attn" in key:
            key = key.replace("attn", "attention")
        if "fusion_blks" in key:
            key = key.replace("fusion_blks", "fusion_blocks")
        if "bn" in key:
            key = key.replace("bn", "batch_norm")
        state_dict[key] = val

    # rename keys
    rename_keys = create_rename_keys(config)
    for src, dest in rename_keys:
        rename_key(state_dict, src, dest)

    # create model
    processor = VitMatteImageProcessor()
    model = VitMatteForImageMatting(config)
    model.eval()

    # load state dict
    model.load_state_dict(state_dict)

    # verify on dummy image + trimap
    url = "https://github.com/hustvl/ViTMatte/blob/main/demo/bulb_rgb.png?raw=true"
    with httpx.stream("GET", url) as response:
        image = Image.open(BytesIO(response.read())).convert("RGB")
    url = "https://github.com/hustvl/ViTMatte/blob/main/demo/bulb_trimap.png?raw=true"
    with httpx.stream("GET", url) as response:
        trimap = Image.open(BytesIO(response.read()))

    pixel_values = processor(images=image, trimaps=trimap.convert("L"), return_tensors="pt").pixel_values

    with torch.no_grad():
        alphas = model(pixel_values).alphas

    if model_name == "vitmatte-small-composition-1k":
        expected_slice = torch.tensor([[0.9977, 0.9987, 0.9990], [0.9980, 0.9998, 0.9998], [0.9983, 0.9998, 0.9998]])
    elif model_name == "vitmatte-base-composition-1k":
        expected_slice = torch.tensor([[0.9972, 0.9971, 0.9981], [0.9948, 0.9987, 0.9994], [0.9963, 0.9992, 0.9995]])
    elif model_name == "vitmatte-small-distinctions-646":
        expected_slice = torch.tensor([[0.9880, 0.9970, 0.9972], [0.9960, 0.9996, 0.9997], [0.9963, 0.9996, 0.9997]])
    elif model_name == "vitmatte-base-distinctions-646":
        expected_slice = torch.tensor([[0.9963, 0.9998, 0.9999], [0.9995, 1.0000, 1.0000], [0.9992, 0.9999, 1.0000]])

    assert torch.allclose(alphas[0, 0, :3, :3], expected_slice, atol=1e-4)
    print("Looks ok!")

    if pytorch_dump_folder_path is not None:
        print(f"Saving model and processor of {model_name} to {pytorch_dump_folder_path}")
        model.save_pretrained(pytorch_dump_folder_path)
        processor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        print(f"Pushing model and processor for {model_name} to hub")
        model.push_to_hub(f"hustvl/{model_name}")
        processor.push_to_hub(f"hustvl/{model_name}")