def _get_hf_download_state(
    model_names: list[str] | None = None,
) -> tuple[int, bool] | None:
    """Return (total_bytes, has_incomplete) for the HF Hub cache, or None on error.

    When *model_names* is provided, only those models' ``blobs/``
    directories are checked instead of scanning every cached model --
    much faster on systems with many models. Accepts multiple names so
    that LoRA loads can watch both the adapter repo and the base model
    repo simultaneously.

    *has_incomplete* is True when any ``*.incomplete`` files exist in the
    watched blobs directories, indicating that ``huggingface_hub`` is
    actively downloading.

    Returns None if the state cannot be determined (import error,
    permission error, etc.) so callers can skip stall logic.
    """
    try:
        from huggingface_hub.constants import HF_HUB_CACHE

        cache = Path(HF_HUB_CACHE)
        if not cache.exists():
            return (0, False)

        total = 0
        has_incomplete = False
        blobs_dirs: list[Path] = []

        if model_names:
            from utils.paths import resolve_cached_repo_id_case

            for name in model_names:
                if not name:
                    continue
                # Skip local filesystem paths -- HF model IDs use forward
                # slashes (org/model) but never start with / . ~ or contain
                # backslashes. This distinguishes them from absolute paths,
                # relative paths, and Windows paths.
                if name.startswith(("/", ".", "~")) or "\\" in name:
                    continue
                name = resolve_cached_repo_id_case(name)
                # HF cache dir format: models--org--name (slashes -> --)
                cache_dir_name = "models--" + name.replace("/", "--")
                blobs_dir = cache / cache_dir_name / "blobs"
                if blobs_dir.exists():
                    blobs_dirs.append(blobs_dir)
        else:
            blobs_dirs = list(cache.glob("models--*/blobs"))

        for bdir in blobs_dirs:
            for f in bdir.iterdir():
                try:
                    if f.is_file():
                        total += f.stat().st_size
                        if f.name.endswith(".incomplete"):
                            has_incomplete = True
                except OSError:
                    pass

        return (total, has_incomplete)
    except Exception as e:
        logger.debug("Failed to determine HF download state: %s", e)
        return None