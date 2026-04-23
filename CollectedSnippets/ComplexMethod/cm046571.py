async def get_dataset_download_progress(
    repo_id: str = Query(
        ..., description = "HuggingFace dataset repo ID, e.g. 'unsloth/LaTeX_OCR'"
    ),
    current_subject: str = Depends(get_current_subject),
):
    """Return download progress for a HuggingFace dataset repo.

    Mirrors ``GET /api/models/download-progress`` but scans the
    ``datasets--owner--name`` cache directory under HF_HUB_CACHE.
    Modern ``datasets``/``huggingface_hub`` caches both raw model and
    raw dataset blobs in HF_HUB_CACHE; the ``datasets`` library writes
    its processed Arrow shards elsewhere, but the in-progress *download*
    bytes are observable here. Returns ``cache_path`` so the UI can
    show users where the dataset blobs landed on disk.
    """
    _empty = {
        "downloaded_bytes": 0,
        "expected_bytes": 0,
        "progress": 0,
        "cache_path": None,
    }
    try:
        if not _is_valid_repo_id(repo_id):
            return _empty

        from huggingface_hub import constants as hf_constants

        cache_dir = Path(hf_constants.HF_HUB_CACHE)
        target = f"datasets--{repo_id.replace('/', '--')}".lower()
        completed_bytes = 0
        in_progress_bytes = 0
        cache_path: Optional[str] = None

        if cache_dir.is_dir():
            for entry in cache_dir.iterdir():
                if entry.name.lower() != target:
                    continue
                cache_path = _resolve_hf_cache_realpath(entry)
                blobs_dir = entry / "blobs"
                if not blobs_dir.is_dir():
                    break
                for f in blobs_dir.iterdir():
                    if not f.is_file():
                        continue
                    if f.name.endswith(".incomplete"):
                        in_progress_bytes += f.stat().st_size
                    else:
                        completed_bytes += f.stat().st_size
                break

        downloaded_bytes = completed_bytes + in_progress_bytes
        if downloaded_bytes == 0:
            return {**_empty, "cache_path": cache_path}

        expected_bytes = _get_dataset_size_cached(repo_id)
        if expected_bytes <= 0:
            return {
                "downloaded_bytes": downloaded_bytes,
                "expected_bytes": 0,
                "progress": 0,
                "cache_path": cache_path,
            }

        # Same 95% completion threshold as the model endpoint -- HF blob
        # dedup makes completed_bytes drift slightly under expected_bytes,
        # and inter-file gaps would otherwise look like "done".
        if completed_bytes >= expected_bytes * 0.95:
            progress = 1.0
        else:
            progress = min(downloaded_bytes / expected_bytes, 0.99)
        return {
            "downloaded_bytes": downloaded_bytes,
            "expected_bytes": expected_bytes,
            "progress": round(progress, 3),
            "cache_path": cache_path,
        }
    except Exception as e:
        logger.warning(f"Error checking dataset download progress for {repo_id}: {e}")
        return _empty