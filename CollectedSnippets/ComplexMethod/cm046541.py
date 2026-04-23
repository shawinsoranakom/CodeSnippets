async def list_cached_models(
    current_subject: str = Depends(get_current_subject),
):
    """List non-GGUF model repos downloaded to HF cache, legacy Unsloth cache, and HF default cache."""
    _WEIGHT_EXTENSIONS = (".safetensors", ".bin")

    try:
        cache_scans = _all_hf_cache_scans()

        seen_lower: dict[str, dict] = {}
        for hf_cache in cache_scans:
            for repo_info in hf_cache.repos:
                try:
                    if repo_info.repo_type != "model":
                        continue
                    repo_id = repo_info.repo_id
                    if _repo_has_gguf_files(repo_info):
                        continue
                    total_size = sum(
                        (f.size_on_disk or 0)
                        for rev in repo_info.revisions
                        for f in rev.files
                    )
                    if total_size == 0:
                        continue
                    has_weights = any(
                        f.file_name.endswith(_WEIGHT_EXTENSIONS)
                        for rev in repo_info.revisions
                        for f in rev.files
                    )
                    if not has_weights:
                        continue
                    key = repo_id.lower()
                    existing = seen_lower.get(key)
                    if existing is None or total_size > existing["size_bytes"]:
                        seen_lower[key] = {
                            "repo_id": repo_id,
                            "size_bytes": total_size,
                        }
                except Exception as e:
                    repo_label = getattr(repo_info, "repo_id", "<unknown>")
                    logger.warning(f"Skipping cached model repo {repo_label}: {e}")
                    continue
        cached = sorted(seen_lower.values(), key = lambda c: c["repo_id"])
        return {"cached": cached}
    except Exception as e:
        logger.error(f"Error listing cached models: {e}", exc_info = True)
        return {"cached": []}