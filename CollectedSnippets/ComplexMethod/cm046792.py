def is_local_path(path: str) -> bool:
    """
    Check if path is a local filesystem path vs HuggingFace model identifier.

    Examples:
        True: /home/user/model, C:\\models, ./model, ~/model
        False: unsloth/llama-3.1-8b, microsoft/phi-2
    """
    if not path:
        return False

    # If it exists on disk, treat as local (covers relative paths like "outputs/foo").
    try:
        if Path(normalize_path(path)).expanduser().exists():
            return True
    except Exception:
        pass

    # Obvious HF patterns
    if path.count("/") == 1 and not path.startswith(("/", ".", "~")):
        return False  # Looks like org/model format

    # Filesystem indicators
    return (
        path.startswith(("/", ".", "~"))  # Unix absolute/relative
        or ":" in path  # Windows drive or URL
        or "\\" in path  # Windows separator
        or os.path.isabs(path)  # System-absolute
    )