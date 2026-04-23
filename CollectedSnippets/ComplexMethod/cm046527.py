def _count_model_files(directory: Path, cap: int = 200) -> int:
    """Count GGUF/safetensors files immediately inside *directory*.
    Used to surface a count-hint on the response so the UI can tell
    users that a leaf directory (no subdirs, only weights) is a valid
    "Use this folder" target.

    Bounded by *visited entries*, not by *match count*: in directories
    with many non-model files (or many subdirectories) the scan still
    stops after ``cap`` entries so a UI hint never costs more than a
    bounded directory walk.
    """
    n = 0
    visited = 0
    try:
        for f in directory.iterdir():
            visited += 1
            if visited > cap:
                break
            try:
                if f.is_file():
                    low = f.name.lower()
                    if low.endswith((".gguf", ".safetensors")):
                        n += 1
            except OSError:
                continue
    except PermissionError as e:
        logger.debug("browse-folders: permission denied counting %s: %s", directory, e)
        return 0
    except OSError as e:
        logger.debug("browse-folders: OS error counting %s: %s", directory, e)
        return 0
    return n