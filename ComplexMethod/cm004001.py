def convert_superpoint_checkpoint(checkpoint_url, pytorch_dump_folder_path, save_model, push_to_hub, test_mode=False):
    """
    Copy/paste/tweak model's weights to our SuperPoint structure.
    """

    print("Downloading original model from checkpoint...")
    config = get_superpoint_config()

    # load original state_dict from URL
    original_state_dict = torch.hub.load_state_dict_from_url(checkpoint_url)

    print("Converting model parameters...")
    # rename keys
    rename_keys = create_rename_keys(config, original_state_dict)
    new_state_dict = original_state_dict.copy()
    for src, dest in rename_keys:
        rename_key(new_state_dict, src, dest)

    # Load HuggingFace model
    model = SuperPointForKeypointDetection(config)
    model.load_state_dict(new_state_dict)
    model.eval()
    print("Successfully loaded weights in the model")

    # Check model outputs
    preprocessor = SuperPointImageProcessor()
    inputs = preprocessor(images=prepare_imgs(), return_tensors="pt")
    outputs = model(**inputs)

    # If test_mode is True, we check that the model outputs match the original results
    if test_mode:
        torch.count_nonzero(outputs.mask[0])
        expected_keypoints_shape = (2, 830, 2)
        expected_scores_shape = (2, 830)
        expected_descriptors_shape = (2, 830, 256)

        expected_keypoints_values = torch.tensor([[480.0, 9.0], [494.0, 9.0], [489.0, 16.0]])
        expected_scores_values = torch.tensor([0.0064, 0.0140, 0.0595, 0.0728, 0.5170, 0.0175, 0.1523, 0.2055, 0.0336])
        expected_descriptors_value = torch.tensor(-0.1096)
        assert outputs.keypoints.shape == expected_keypoints_shape
        assert outputs.scores.shape == expected_scores_shape
        assert outputs.descriptors.shape == expected_descriptors_shape

        assert torch.allclose(outputs.keypoints[0, :3], expected_keypoints_values, atol=1e-3)
        assert torch.allclose(outputs.scores[0, :9], expected_scores_values, atol=1e-3)
        assert torch.allclose(outputs.descriptors[0, 0, 0], expected_descriptors_value, atol=1e-3)
        print("Model outputs match the original results!")

    if save_model:
        print("Saving model to local...")
        # Create folder to save model
        if not os.path.isdir(pytorch_dump_folder_path):
            os.mkdir(pytorch_dump_folder_path)

        model.save_pretrained(pytorch_dump_folder_path)
        preprocessor.save_pretrained(pytorch_dump_folder_path)

        model_name = "magic-leap-community/superpoint"
        if push_to_hub:
            print(f"Pushing {model_name} to the hub...")
        model.push_to_hub(model_name)
        preprocessor.push_to_hub(model_name)