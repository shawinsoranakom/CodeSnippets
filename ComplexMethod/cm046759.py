def _has_model_weight_files(model_dir: Path) -> bool:
    """Return True when a directory contains loadable model weights."""
    for item in model_dir.iterdir():
        if not item.is_file():
            continue

        suffix = item.suffix.lower()
        if suffix == ".safetensors":
            return True
        if suffix == ".gguf":
            return "mmproj" not in item.name.lower()
        if suffix == ".bin":
            name = item.name.lower()
            if (
                name.startswith("pytorch_model")
                or name.startswith("model")
                or name.startswith("adapter_model")
                or name.startswith("consolidated")
            ):
                return True
    return False