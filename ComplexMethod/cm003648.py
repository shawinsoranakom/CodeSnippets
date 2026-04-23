def write_model(model_name, output_dir, push_to_hub, verify_logits):
    """
    Copy/paste/tweak model's weights to our IJEPA structure.
    """

    # define default IJEPA configuration
    config = get_ijepa_config(model_name)

    checkpoint_mapping = {
        "ijepa_vith14_1k": "https://dl.fbaipublicfiles.com/ijepa/IN1K-vit.h.14-300e.pth.tar",
        "ijepa_vith14_22k": "https://dl.fbaipublicfiles.com/ijepa/IN22K-vit.h.14-900e.pth.tar",
        "ijepa_vith16_1k": "https://dl.fbaipublicfiles.com/ijepa/IN1K-vit.h.16-448px-300e.pth.tar",
        "ijepa_vitg16_22k": "https://dl.fbaipublicfiles.com/ijepa/IN22K-vit.g.16-600e.pth.tar",
    }

    # Load original checkpoint
    checkpoint_url = checkpoint_mapping[model_name]
    original_state_dict = torch.hub.load_state_dict_from_url(checkpoint_url, map_location="cpu")["encoder"]
    original_state_dict = {k.replace("module.", ""): v for k, v in original_state_dict.items()}

    # Rename keys
    state_dict = original_state_dict.copy()
    new_keys = convert_old_keys_to_new_keys(state_dict.keys())
    for old_key, new_key in new_keys.items():
        rename_key(state_dict, old_key, new_key)
    read_in_q_k_v(state_dict, config)

    # load HuggingFace model
    model = IJepaModel(config, add_pooling_layer=False).eval()
    model.load_state_dict(state_dict)
    size = {"height": config.image_size, "width": config.image_size}
    image_processor = ViTImageProcessor(size=size)

    if verify_logits:
        # Check outputs on an image, prepared by ViTImageProcessor
        encoding = image_processor(images=prepare_img(), return_tensors="pt")
        pixel_values = encoding["pixel_values"]
        with torch.no_grad():
            outputs = model(pixel_values)

        expected_slices = {
            "ijepa_vith14_1k": torch.Tensor(
                [[-0.0621, -0.0054, -2.7513], [-0.1952, 0.0909, -3.9536], [0.0942, -0.0331, -1.2833]]
            ),
            "ijepa_vith14_22k": torch.Tensor(
                [[0.0358, -0.0045, -0.2154], [0.0418, -0.0246, 0.0108], [0.2529, -0.0345, -0.0246]]
            ),
            "ijepa_vith16_1k": torch.Tensor(
                [[0.5145, -0.1259, 0.0615], [0.1132, 0.0028, -0.0496], [1.1586, -0.0056, -0.0387]]
            ),
            "ijepa_vitg16_22k": torch.Tensor(
                [[0.0512, -0.0510, -0.0649], [0.1972, 0.0380, -0.0790], [0.1667, -0.0834, -0.1240]]
            ),
        }

        assert torch.allclose(
            expected_slices[model_name],
            outputs.last_hidden_state[0, :3, :3],
            atol=1e-4,
        )

    if output_dir:
        Path(output_dir).mkdir(exist_ok=True)
        print(f"Saving model {model_name} to {output_dir}")
        image_processor.save_pretrained(output_dir)
        model.save_pretrained(output_dir)

    if push_to_hub:
        image_processor.push_to_hub(repo_id=f"jmtzt/{model_name}")
        model.push_to_hub(repo_id=f"jmtzt/{model_name}")

    if output_dir:
        del model, state_dict
        gc.collect()
        print("Reloading the model to check if it's saved correctly.")
        IJepaModel.from_pretrained(output_dir, device_map="auto")
        print("Model reloaded successfully.")