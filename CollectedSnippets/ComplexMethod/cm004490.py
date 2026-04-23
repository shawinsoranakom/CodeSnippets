def convert_movilevit_checkpoint(model_name, checkpoint_path, pytorch_dump_folder_path, push_to_hub=False):
    """
    Copy/paste/tweak model's weights to our MobileNetV2 structure.
    """
    config = get_mobilenet_v2_config(model_name)

    # Load 🤗 model
    if model_name.startswith("deeplabv3_"):
        model = MobileNetV2ForSemanticSegmentation(config).eval()
    else:
        model = MobileNetV2ForImageClassification(config).eval()

    # Load weights from TensorFlow checkpoint
    load_tf_weights_in_mobilenet_v2(model, config, checkpoint_path)

    # Check outputs on an image, prepared by MobileNetV2ImageProcessor
    image_processor = MobileNetV2ImageProcessor(
        crop_size={"width": config.image_size, "height": config.image_size},
        size={"shortest_edge": config.image_size + 32},
    )
    encoding = image_processor(images=prepare_img(), return_tensors="pt")
    outputs = model(**encoding)
    logits = outputs.logits

    if model_name.startswith("deeplabv3_"):
        assert logits.shape == (1, 21, 65, 65)

        if model_name == "deeplabv3_mobilenet_v2_1.0_513":
            expected_logits = torch.tensor(
                [
                    [[17.5790, 17.7581, 18.3355], [18.3257, 18.4230, 18.8973], [18.6169, 18.8650, 19.2187]],
                    [[-2.1595, -2.0977, -2.3741], [-2.4226, -2.3028, -2.6835], [-2.7819, -2.5991, -2.7706]],
                    [[4.2058, 4.8317, 4.7638], [4.4136, 5.0361, 4.9383], [4.5028, 4.9644, 4.8734]],
                ]
            )

        else:
            raise ValueError(f"Unknown model name: {model_name}")

        assert torch.allclose(logits[0, :3, :3, :3], expected_logits, atol=1e-4)
    else:
        assert logits.shape == (1, 1001)

        if model_name == "mobilenet_v2_1.4_224":
            expected_logits = torch.tensor([0.0181, -1.0015, 0.4688])
        elif model_name == "mobilenet_v2_1.0_224":
            expected_logits = torch.tensor([0.2445, -1.1993, 0.1905])
        elif model_name == "mobilenet_v2_0.75_160":
            expected_logits = torch.tensor([0.2482, 0.4136, 0.6669])
        elif model_name == "mobilenet_v2_0.35_96":
            expected_logits = torch.tensor([0.1451, -0.4624, 0.7192])
        else:
            expected_logits = None

        if expected_logits is not None:
            assert torch.allclose(logits[0, :3], expected_logits, atol=1e-4)

    Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
    print(f"Saving model {model_name} to {pytorch_dump_folder_path}")
    model.save_pretrained(pytorch_dump_folder_path)
    print(f"Saving image processor to {pytorch_dump_folder_path}")
    image_processor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        print("Pushing to the hub...")
        repo_id = "google/" + model_name
        image_processor.push_to_hub(repo_id)
        model.push_to_hub(repo_id)