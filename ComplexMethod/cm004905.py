def check_outputs(model_path, huggingface_repo_id):
    """Compares outputs between original and converted models."""
    print("\nChecking model outputs...")

    # Load original model
    tfm = timesfm.TimesFm(
        hparams=timesfm.TimesFmHparams(
            backend="cuda" if torch.cuda.is_available() else "cpu",
            per_core_batch_size=32,
            horizon_len=128,
            input_patch_len=32,
            output_patch_len=128,
            num_layers=50,
            context_len=2048,
            model_dims=1280,
            use_positional_embedding=False,
            point_forecast_mode="mean",
        ),
        checkpoint=timesfm.TimesFmCheckpoint(huggingface_repo_id=huggingface_repo_id),
    )

    # Load converted model
    converted_model = TimesFmModelForPrediction.from_pretrained(
        model_path,
        dtype=torch.bfloat16,
        attn_implementation="sdpa",
    ).to("cuda" if torch.cuda.is_available() else "cpu")
    converted_model.eval()  # Set to evaluation mode

    # Create test inputs
    forecast_input = [
        np.sin(np.linspace(0, 20, 100)),
        np.sin(np.linspace(0, 20, 200)),
        np.sin(np.linspace(0, 20, 400)),
    ]
    frequency_input = [0, 1, 2]

    # Get predictions from original model
    point_forecast_orig, quantile_forecast_orig = tfm.forecast(
        forecast_input,
        freq=frequency_input,
    )

    # Convert inputs to sequence of tensors
    forecast_input_tensor = [
        torch.tensor(ts, dtype=torch.bfloat16).to("cuda" if torch.cuda.is_available() else "cpu")
        for ts in forecast_input
    ]
    frequency_input_tensor = torch.tensor(frequency_input, dtype=torch.long).to(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    # Get predictions from converted model
    with torch.no_grad():
        outputs = converted_model(past_values=forecast_input_tensor, freq=frequency_input_tensor, return_dict=True)
        point_forecast_conv = outputs.mean_predictions.float().cpu().numpy()
        quantile_forecast_conv = outputs.full_predictions.float().cpu().numpy()

    # Compare outputs
    point_forecast_diff = np.abs(point_forecast_orig - point_forecast_conv)
    quantile_forecast_diff = np.abs(quantile_forecast_orig - quantile_forecast_conv)

    max_point_diff = point_forecast_diff.max()
    mean_point_diff = point_forecast_diff.mean()
    max_quantile_diff = quantile_forecast_diff.max()
    mean_quantile_diff = quantile_forecast_diff.mean()

    print("\nOutput comparison:")
    print(f"Point forecast - Max difference: {max_point_diff:.6f}")
    print(f"Point forecast - Mean difference: {mean_point_diff:.6f}")
    print(f"Quantile forecast - Max difference: {max_quantile_diff:.6f}")
    print(f"Quantile forecast - Mean difference: {mean_quantile_diff:.6f}")

    # Define acceptable thresholds
    POINT_THRESHOLD = 1e-5
    QUANTILE_THRESHOLD = 1e-5

    if max_point_diff > POINT_THRESHOLD or max_quantile_diff > QUANTILE_THRESHOLD:
        raise ValueError(
            f"Output mismatch detected!\n"
            f"Point forecast max diff: {max_point_diff} (threshold: {POINT_THRESHOLD})\n"
            f"Quantile forecast max diff: {max_quantile_diff} (threshold: {QUANTILE_THRESHOLD})"
        )

    print("\n✓ All outputs match within acceptable tolerance!")

    # Optional: Print shapes for verification
    print("\nOutput shapes:")
    print(f"Original point forecast: {point_forecast_orig.shape}")
    print(f"Converted point forecast: {point_forecast_conv.shape}")
    print(f"Original quantile forecast: {quantile_forecast_orig.shape}")
    print(f"Converted quantile forecast: {quantile_forecast_conv.shape}")