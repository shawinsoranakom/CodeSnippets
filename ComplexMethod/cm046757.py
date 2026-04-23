def detect_gguf_model(path: str) -> Optional[str]:
    """
    Check if the given local path is or contains a GGUF model file.

    Handles two cases:
    1. path is a direct .gguf file path
    2. path is a directory containing .gguf files

    Skips mmproj (vision projection) files — those must be passed via
    ``--mmproj``, not ``-m``.  Use :func:`detect_mmproj_file` instead.

    Returns the full path to the .gguf file if found, None otherwise.
    For HuggingFace repo detection, use detect_gguf_model_remote() instead.
    """
    p = Path(path)

    # Case 1: direct .gguf file
    if p.suffix.lower() == ".gguf" and p.is_file():
        if _is_mmproj(p.name):
            return None
        # Use absolute (not resolve) to preserve symlink names -- e.g.
        # Ollama .studio_links/model.gguf -> blobs/sha256-... should
        # keep the readable symlink name, not the opaque blob hash.
        return str(p.absolute())

    # Case 2: directory containing .gguf files (skip mmproj)
    if p.is_dir():
        gguf_files = sorted(
            (f for f in _iter_gguf_files(p) if not _is_mmproj(f.name)),
            key = lambda f: f.stat().st_size,
            reverse = True,
        )
        if gguf_files:
            return str(gguf_files[0].resolve())

    return None