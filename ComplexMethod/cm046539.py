async def get_download_progress(
    repo_id: str = Query(..., description = "HuggingFace repo ID"),
    current_subject: str = Depends(get_current_subject),
):
    """Return download progress for any HuggingFace model repo.

    Checks the local HF cache for completed blobs and in-progress
    (.incomplete) downloads. Uses the HF API to determine the expected
    total size on the first call, then caches it for subsequent polls.
    Also returns ``cache_path``: the realpath of the snapshot directory
    (or the cache repo root if no snapshot exists yet) so the UI can
    show users where the weights actually live on disk.
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
        target = f"models--{repo_id.replace('/', '--')}".lower()
        completed_bytes = 0
        in_progress_bytes = 0
        cache_path: Optional[str] = None

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

        # Get expected size from HF API (cached per repo_id)
        expected_bytes = _get_repo_size_cached(repo_id)
        if expected_bytes <= 0:
            # Cannot determine total; report bytes only, no percentage
            return {
                "downloaded_bytes": downloaded_bytes,
                "expected_bytes": 0,
                "progress": 0,
                "cache_path": cache_path,
            }

        # Use 95% threshold for completion (blob deduplication can make
        # completed_bytes differ slightly from expected_bytes).
        # Do NOT use "no .incomplete files" as a completion signal --
        # HF downloads files sequentially, so between files there are
        # no .incomplete files even though the download is far from done.
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
        logger.warning(f"Error checking download progress for {repo_id}: {e}")
        return _empty