def verify_model_outputs(model, model_name, device):
    images = prepare_imgs()
    preprocessor = SuperGlueImageProcessor()
    inputs = preprocessor(images=images, return_tensors="pt").to(device)
    model.to(device)
    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True, output_attentions=True)

    predicted_matches_values = outputs.matches[0, 0, :10]
    predicted_matching_scores_values = outputs.matching_scores[0, 0, :10]

    predicted_number_of_matches = torch.sum(outputs.matches[0][0] != -1).item()

    if "outdoor" in model_name:
        expected_max_number_keypoints = 865
        expected_matches_shape = torch.Size((len(images), 2, expected_max_number_keypoints))
        expected_matching_scores_shape = torch.Size((len(images), 2, expected_max_number_keypoints))

        expected_matches_values = torch.tensor(
            [125, 630, 137, 138, 136, 143, 135, -1, -1, 153], dtype=torch.int64, device=device
        )
        expected_matching_scores_values = torch.tensor(
            [0.9899, 0.0033, 0.9897, 0.9889, 0.9879, 0.7464, 0.7109, 0, 0, 0.9841], device=device
        )

        expected_number_of_matches = 281
    elif "indoor" in model_name:
        expected_max_number_keypoints = 865
        expected_matches_shape = torch.Size((len(images), 2, expected_max_number_keypoints))
        expected_matching_scores_shape = torch.Size((len(images), 2, expected_max_number_keypoints))

        expected_matches_values = torch.tensor(
            [125, 144, 137, 138, 136, 155, 135, -1, -1, 153], dtype=torch.int64, device=device
        )
        expected_matching_scores_values = torch.tensor(
            [0.9694, 0.0010, 0.9006, 0.8753, 0.8521, 0.5688, 0.6321, 0.0, 0.0, 0.7235], device=device
        )

        expected_number_of_matches = 282

    assert outputs.matches.shape == expected_matches_shape
    assert outputs.matching_scores.shape == expected_matching_scores_shape

    assert torch.allclose(predicted_matches_values, expected_matches_values, atol=1e-4)
    assert torch.allclose(predicted_matching_scores_values, expected_matching_scores_values, atol=1e-4)

    assert predicted_number_of_matches == expected_number_of_matches