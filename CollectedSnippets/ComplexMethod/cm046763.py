def load_model_defaults(model_name: str) -> Dict[str, Any]:
    """
    Load default training parameters for a model from YAML file.

    Args:
        model_name: Model identifier (e.g., "unsloth/Meta-Llama-3.1-8B-bnb-4bit")

    Returns:
        Dictionary with default parameters from YAML file, or empty dict if not found

    The function looks for a YAML file in configs/model_defaults/ (including subfolders)
    based on the model name or its aliases from MODEL_NAME_MAPPING.
    If no specific file exists, it falls back to default.yaml.
    """
    try:
        # Get the script directory to locate configs
        script_dir = Path(__file__).parent.parent.parent
        defaults_dir = script_dir / "assets" / "configs" / "model_defaults"

        # First, check if model is in the mapping
        if model_name.lower() in _REVERSE_MODEL_MAPPING:
            canonical_file = _REVERSE_MODEL_MAPPING[model_name.lower()]
            # Search in subfolders and root
            for config_path in defaults_dir.rglob(canonical_file):
                if config_path.is_file():
                    with open(config_path, "r", encoding = "utf-8") as f:
                        config = yaml.safe_load(f) or {}
                        logger.info(
                            f"Loaded model defaults from {config_path} (via mapping)"
                        )
                        return config

        # If model_name is a local path (e.g. /home/.../Spark-TTS-0.5B/LLM from
        # adapter_config.json, or C:\Users\...\model on Windows), try matching
        # the last 1-2 path components against the registry
        # (e.g. "Spark-TTS-0.5B/LLM").
        _is_local_path = is_local_path(model_name)
        # Normalize Windows backslash paths so Path().parts splits correctly
        # on POSIX/WSL hosts (pathlib treats backslashes as literals on Linux).
        _normalized = normalize_path(model_name) if _is_local_path else model_name
        if model_name.lower() not in _REVERSE_MODEL_MAPPING and _is_local_path:
            parts = Path(_normalized).parts
            for depth in [2, 1]:
                if len(parts) >= depth:
                    suffix = "/".join(parts[-depth:])
                    if suffix.lower() in _REVERSE_MODEL_MAPPING:
                        canonical_file = _REVERSE_MODEL_MAPPING[suffix.lower()]
                        for config_path in defaults_dir.rglob(canonical_file):
                            if config_path.is_file():
                                with open(config_path, "r", encoding = "utf-8") as f:
                                    config = yaml.safe_load(f) or {}
                                    logger.info(
                                        f"Loaded model defaults from {config_path} (via path suffix '{suffix}')"
                                    )
                                    return config

        # Try exact model name match (for backward compatibility).
        # For local filesystem paths, use only the directory basename to
        # avoid passing absolute paths (e.g. C:\...) into rglob which
        # raises "Non-relative patterns are unsupported" on Windows.
        _lookup_name = Path(_normalized).name if _is_local_path else model_name
        model_filename = _lookup_name.replace("/", "_") + ".yaml"
        # Search in subfolders and root
        for config_path in defaults_dir.rglob(model_filename):
            if config_path.is_file():
                with open(config_path, "r", encoding = "utf-8") as f:
                    config = yaml.safe_load(f) or {}
                    logger.info(f"Loaded model defaults from {config_path}")
                    return config

        # Fall back to default.yaml
        default_config_path = defaults_dir / "default.yaml"
        if default_config_path.exists():
            with open(default_config_path, "r", encoding = "utf-8") as f:
                config = yaml.safe_load(f) or {}
                logger.info(f"Loaded default model defaults from {default_config_path}")
                return config

        logger.warning(f"No default config found for model {model_name}")
        return {}

    except Exception as e:
        logger.error(f"Error loading model defaults for {model_name}: {e}")
        return {}