def _has_direct_model_signal(directory: Path) -> bool:
    """Return True if *directory* has an immediate child that signals
    it holds a model: a GGUF/safetensors/config.json file, or a
    `models--*` subdir (HF hub cache). Bounded by
    ``_BROWSE_MODEL_HINT_PROBE`` to stay fast."""
    try:
        it = directory.iterdir()
    except OSError:
        return False
    try:
        for i, child in enumerate(it):
            if i >= _BROWSE_MODEL_HINT_PROBE:
                break
            try:
                name = child.name
                if child.is_file():
                    low = name.lower()
                    if low.endswith((".gguf", ".safetensors")):
                        return True
                    if low in ("config.json", "adapter_config.json"):
                        return True
                elif child.is_dir() and name.startswith("models--"):
                    return True
            except OSError:
                continue
    except OSError:
        return False
    return False