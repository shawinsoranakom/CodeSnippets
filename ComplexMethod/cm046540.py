async def list_cached_gguf(
    current_subject: str = Depends(get_current_subject),
):
    """List GGUF repos downloaded to HF cache, legacy Unsloth cache, and HF default cache."""
    try:
        cache_scans = _all_hf_cache_scans()

        seen_lower: dict[str, dict] = {}
        for hf_cache in cache_scans:
            for repo_info in hf_cache.repos:
                try:
                    if repo_info.repo_type != "model":
                        continue
                    repo_id = repo_info.repo_id
                    total_size = _repo_gguf_size_bytes(repo_info)
                    if total_size == 0:
                        continue
                    key = repo_id.lower()
                    existing = seen_lower.get(key)
                    if existing is None or total_size > existing["size_bytes"]:
                        seen_lower[key] = {
                            "repo_id": repo_id,
                            "size_bytes": total_size,
                            "cache_path": str(repo_info.repo_path),
                        }
                except Exception as e:
                    repo_label = getattr(repo_info, "repo_id", "<unknown>")
                    logger.warning(f"Skipping cached GGUF repo {repo_label}: {e}")
                    continue
        cached = sorted(seen_lower.values(), key = lambda c: c["repo_id"])
        return {"cached": cached}
    except Exception as e:
        logger.error(f"Error listing cached GGUF repos: {e}", exc_info = True)
        return {"cached": []}