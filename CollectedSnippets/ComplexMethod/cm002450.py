def find_sentencepiece_model_file(pretrained_model_name_or_path, **kwargs):
    """
    Find any .model file (SentencePiece model) in the model directory or Hub repo.

    Tries known filenames first ("tokenizer.model", "spm.model"), then scans local dir,
    and as a last resort lists files on the Hub to find any .model.

    Returns the filename (str) relative to the repo root or directory if found, else None.
    """
    from .utils.hub import has_file

    # Try common names first
    for candidate in ("tokenizer.model", "spm.model"):
        try:
            if has_file(
                pretrained_model_name_or_path,
                candidate,
                revision=kwargs.get("revision"),
                token=kwargs.get("token"),
                cache_dir=kwargs.get("cache_dir"),
                local_files_only=kwargs.get("local_files_only", False),
            ):
                return candidate
        except Exception:
            # TODO: tighten to OSError / ProxyError
            continue

    subfolder = kwargs.get("subfolder", "")
    local_files_only = kwargs.get("local_files_only", False)

    # Local directory scan
    if os.path.isdir(pretrained_model_name_or_path):
        dir_path = (
            os.path.join(pretrained_model_name_or_path, subfolder) if subfolder else pretrained_model_name_or_path
        )
        if os.path.isdir(dir_path):
            for filename in os.listdir(dir_path):
                if filename.endswith(".model"):
                    return filename if not subfolder else os.path.join(subfolder, filename)

    # Hub listing if allowed
    if not local_files_only:
        try:
            from huggingface_hub import list_repo_tree

            entries = list_repo_tree(
                repo_id=pretrained_model_name_or_path,
                revision=kwargs.get("revision"),
                path_in_repo=subfolder if subfolder else None,
                recursive=False,
                token=kwargs.get("token"),
            )
            for entry in entries:
                if entry.path.endswith(".model"):
                    return entry.path if not subfolder else entry.path.removeprefix(f"{subfolder}/")
        except Exception as e:
            # TODO: tighten exception class
            logger.debug(f"Could not list Hub repository files: {e}")

    return None