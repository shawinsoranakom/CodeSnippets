def convert_movilevit_checkpoint(mobilevit_name, checkpoint_path, pytorch_dump_folder_path, push_to_hub=False):
    """
    Copy/paste/tweak model's weights to our MobileViT structure.
    """
    config = get_mobilevit_config(mobilevit_name)

    # load original state_dict
    state_dict = torch.load(checkpoint_path, map_location="cpu", weights_only=True)

    # load 🤗 model
    if mobilevit_name.startswith("deeplabv3_"):
        model = MobileViTForSemanticSegmentation(config).eval()
    else:
        model = MobileViTForImageClassification(config).eval()

    new_state_dict = convert_state_dict(state_dict, model)
    model.load_state_dict(new_state_dict)

    # Check outputs on an image, prepared by MobileViTImageProcessor
    image_processor = MobileViTImageProcessor(crop_size=config.image_size, size=config.image_size + 32)
    encoding = image_processor(images=prepare_img(), return_tensors="pt")
    outputs = model(**encoding)
    logits = outputs.logits

    if mobilevit_name.startswith("deeplabv3_"):
        assert logits.shape == (1, 21, 32, 32)

        if mobilevit_name == "deeplabv3_mobilevit_s":
            expected_logits = torch.tensor(
                [
                    [[6.2065, 6.1292, 6.2070], [6.1079, 6.1254, 6.1747], [6.0042, 6.1071, 6.1034]],
                    [[-6.9253, -6.8653, -7.0398], [-7.3218, -7.3983, -7.3670], [-7.1961, -7.2482, -7.1569]],
                    [[-4.4723, -4.4348, -4.3769], [-5.3629, -5.4632, -5.4598], [-5.1587, -5.3402, -5.5059]],
                ]
            )
        elif mobilevit_name == "deeplabv3_mobilevit_xs":
            expected_logits = torch.tensor(
                [
                    [[5.4449, 5.5733, 5.6314], [5.1815, 5.3930, 5.5963], [5.1656, 5.4333, 5.4853]],
                    [[-9.4423, -9.7766, -9.6714], [-9.1581, -9.5720, -9.5519], [-9.1006, -9.6458, -9.5703]],
                    [[-7.7721, -7.3716, -7.1583], [-8.4599, -8.0624, -7.7944], [-8.4172, -7.8366, -7.5025]],
                ]
            )
        elif mobilevit_name == "deeplabv3_mobilevit_xxs":
            expected_logits = torch.tensor(
                [
                    [[6.9811, 6.9743, 7.3123], [7.1777, 7.1931, 7.3938], [7.5633, 7.8050, 7.8901]],
                    [[-10.5536, -10.2332, -10.2924], [-10.2336, -9.8624, -9.5964], [-10.8840, -10.8158, -10.6659]],
                    [[-3.4938, -3.0631, -2.8620], [-3.4205, -2.8135, -2.6875], [-3.4179, -2.7945, -2.8750]],
                ]
            )
        else:
            raise ValueError(f"Unknown mobilevit_name: {mobilevit_name}")

        assert torch.allclose(logits[0, :3, :3, :3], expected_logits, atol=1e-4)
    else:
        assert logits.shape == (1, 1000)

        if mobilevit_name == "mobilevit_s":
            expected_logits = torch.tensor([-0.9866, 0.2392, -1.1241])
        elif mobilevit_name == "mobilevit_xs":
            expected_logits = torch.tensor([-2.4761, -0.9399, -1.9587])
        elif mobilevit_name == "mobilevit_xxs":
            expected_logits = torch.tensor([-1.9364, -1.2327, -0.4653])
        else:
            raise ValueError(f"Unknown mobilevit_name: {mobilevit_name}")

        assert torch.allclose(logits[0, :3], expected_logits, atol=1e-4)

    Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
    print(f"Saving model {mobilevit_name} to {pytorch_dump_folder_path}")
    model.save_pretrained(pytorch_dump_folder_path)
    print(f"Saving image processor to {pytorch_dump_folder_path}")
    image_processor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        model_mapping = {
            "mobilevit_s": "mobilevit-small",
            "mobilevit_xs": "mobilevit-x-small",
            "mobilevit_xxs": "mobilevit-xx-small",
            "deeplabv3_mobilevit_s": "deeplabv3-mobilevit-small",
            "deeplabv3_mobilevit_xs": "deeplabv3-mobilevit-x-small",
            "deeplabv3_mobilevit_xxs": "deeplabv3-mobilevit-xx-small",
        }

        print("Pushing to the hub...")
        model_name = model_mapping[mobilevit_name]
        image_processor.push_to_hub(model_name, organization="apple")
        model.push_to_hub(model_name, organization="apple")