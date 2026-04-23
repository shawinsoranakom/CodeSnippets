def extract_nemo_archive(nemo_file_path: str, extract_dir: str) -> dict[str, str]:
    """
    Extract .nemo file (tar archive) and return paths to important files.

    Args:
        nemo_file_path: Path to .nemo file
        extract_dir: Directory to extract to

    Returns:
        Dictionary with paths to model.pt, model_config.yaml, etc.
    """
    print(f"Extracting NeMo archive: {nemo_file_path}")

    with tarfile.open(nemo_file_path, "r", encoding="utf-8") as tar:
        tar.extractall(extract_dir)

    # Log all extracted files for debugging
    all_files = []
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            file_path = os.path.join(root, file)
            all_files.append(file_path)

    print(f"All extracted files: {[os.path.basename(f) for f in all_files]}")

    # Find important files with more robust detection
    model_files = {}
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            file_path = os.path.join(root, file)
            file_lower = file.lower()

            # Look for model weights with various common names
            if (
                file.endswith(".pt")
                or file.endswith(".pth")
                or file.endswith(".ckpt")
                or file.endswith(".bin")
                or "model" in file_lower
                and ("weight" in file_lower or "state" in file_lower)
                or file_lower == "model.pt"
                or file_lower == "pytorch_model.bin"
                or file_lower == "model_weights.ckpt"
            ):
                model_files["model_weights"] = file_path
                print(f"Found model weights: {file}")

            # Look for config files
            elif (
                file == "model_config.yaml"
                or file == "config.yaml"
                or (file.endswith(".yaml") and "config" in file_lower)
            ):
                if "model_config" not in model_files:  # Prefer model_config.yaml
                    model_files["model_config"] = file_path
                    print(f"Found config file: {file}")
                if file == "model_config.yaml":
                    model_files["model_config"] = file_path  # Override with preferred name

            # Look for vocabulary files
            elif (
                file.endswith(".vocab")
                or file.endswith(".model")
                or file.endswith(".txt")
                or ("tokenizer" in file_lower and (file.endswith(".vocab") or file.endswith(".model")))
            ):
                # Prefer .vocab files over others
                if "tokenizer_model_file" not in model_files or file.endswith(".model"):
                    model_files["tokenizer_model_file"] = file_path
                    print(f"Found tokenizer model file: {file}")
                else:
                    print(f"Found additional vocabulary file (using existing): {file}")

    print(f"Found model files: {list(model_files.keys())}")

    # Validate that we found the required files
    if "model_weights" not in model_files:
        raise FileNotFoundError(
            f"Could not find model weights file in {nemo_file_path}. "
            f"Expected files with extensions: .pt, .pth, .ckpt, .bin. "
            f"Found files: {[os.path.basename(f) for f in all_files]}"
        )

    if "model_config" not in model_files:
        raise FileNotFoundError(
            f"Could not find model config file in {nemo_file_path}. "
            f"Expected: model_config.yaml or config.yaml. "
            f"Found files: {[os.path.basename(f) for f in all_files]}"
        )

    return model_files