async def get_gguf_download_progress(
    repo_id: str = Query(..., description = "HuggingFace repo ID"),
    variant: str = Query("", description = "Quantization variant (e.g. UD-TQ1_0)"),
    expected_bytes: int = Query(0, description = "Expected total download size in bytes"),
    current_subject: str = Depends(get_current_subject),
):
    """Return download progress by checking cached GGUF files for a specific variant.

    Tracks completed shard downloads in snapshots and in-progress downloads
    in the blobs directory (incomplete files).
    """
    try:
        if not _is_valid_repo_id(repo_id):
            return {
                "downloaded_bytes": 0,
                "expected_bytes": expected_bytes,
                "progress": 0,
            }

        from huggingface_hub import constants as hf_constants

        cache_dir = Path(hf_constants.HF_HUB_CACHE)
        target = f"models--{repo_id.replace('/', '--')}".lower()
        variant_lower = variant.lower().replace("-", "").replace("_", "")
        downloaded_bytes = 0
        in_progress_bytes = 0
        for entry in cache_dir.iterdir():
            if entry.name.lower() == target:
                # Count completed .gguf files matching this variant in snapshots
                for f in _iter_gguf_paths(entry):
                    fname = f.name.lower().replace("-", "").replace("_", "")
                    if not variant_lower or variant_lower in fname:
                        downloaded_bytes += f.stat().st_size
                # Check blobs for in-progress downloads (.incomplete files)
                blobs_dir = entry / "blobs"
                if blobs_dir.is_dir():
                    for f in blobs_dir.iterdir():
                        if f.is_file() and f.name.endswith(".incomplete"):
                            in_progress_bytes += f.stat().st_size
                break

        total_progress_bytes = downloaded_bytes + in_progress_bytes
        progress = (
            min(total_progress_bytes / expected_bytes, 0.99)
            if expected_bytes > 0
            else 0
        )
        # Only report 1.0 when all bytes are in completed files (not in-progress)
        if expected_bytes > 0 and downloaded_bytes >= expected_bytes:
            progress = 1.0
        return {
            "downloaded_bytes": total_progress_bytes,
            "expected_bytes": expected_bytes,
            "progress": round(progress, 3),
        }
    except Exception:
        return {"downloaded_bytes": 0, "expected_bytes": expected_bytes, "progress": 0}