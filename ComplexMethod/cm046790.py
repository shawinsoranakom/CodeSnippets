def _has_specific_yaml(model_identifier: str) -> bool:
    """Check if a model has its own YAML config (not just default.yaml)."""
    from utils.models.model_config import _REVERSE_MODEL_MAPPING

    script_dir = Path(__file__).parent.parent.parent
    defaults_dir = script_dir / "assets" / "configs" / "model_defaults"

    # Check the mapping
    if model_identifier.lower() in _REVERSE_MODEL_MAPPING:
        return True

    # For local filesystem paths (e.g. C:\Users\...\model on Windows),
    # normalize backslashes so Path().parts splits correctly on POSIX/WSL,
    # then try matching the last 1-2 path components against the registry
    # (mirrors the logic in load_model_defaults).
    _is_local = is_local_path(model_identifier)
    _normalized = normalize_path(model_identifier) if _is_local else model_identifier

    if _is_local:
        parts = Path(_normalized).parts
        for depth in (2, 1):
            if len(parts) >= depth:
                suffix = "/".join(parts[-depth:])
                if suffix.lower() in _REVERSE_MODEL_MAPPING:
                    return True
        _lookup = Path(_normalized).name
    else:
        _lookup = model_identifier

    # Check for exact filename match (basename for local paths to avoid
    # passing absolute paths into rglob which raises
    # "Non-relative patterns are unsupported" on Windows).
    model_filename = _lookup.replace("/", "_") + ".yaml"
    for config_path in defaults_dir.rglob(model_filename):
        if config_path.is_file():
            return True

    return False