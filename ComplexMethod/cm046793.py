def resolve_cached_repo_id_case(model_name: str, use_memo: bool = True) -> str:
    """Resolve repo_id to the exact casing already present in local HF cache.

    Policy: prefer the requested/canonical repo_id, but if a case-variant already
    exists in local HF cache, reuse that exact cached spelling. This avoids
    duplicate downloads while preserving user intent whenever possible.
    """
    _CACHE_CASE_RESOLUTION_STATS["calls"] += 1

    if not model_name or "/" not in model_name:
        _CACHE_CASE_RESOLUTION_STATS["fallbacks"] += 1
        return model_name

    cache_dir = _hf_hub_cache_dir()
    if not cache_dir.exists():
        _CACHE_CASE_RESOLUTION_STATS["fallbacks"] += 1
        return model_name

    expected_dir = f"models--{model_name.replace('/', '--')}"

    # Always check the exact-case path first so a newly-appeared exact match
    # wins over any previously memoized variant.
    exact_path = cache_dir / expected_dir
    if exact_path.is_dir():
        if use_memo:
            _CACHE_CASE_RESOLUTION_MEMO[model_name] = model_name
        _CACHE_CASE_RESOLUTION_STATS["exact_hits"] += 1
        return model_name

    # Validate memoized entries still exist on disk before returning them.
    # This prevents stale results when cache dirs are deleted/recreated.
    if use_memo:
        cached = _CACHE_CASE_RESOLUTION_MEMO.get(model_name)
        if cached is not None:
            cached_path = cache_dir / f"models--{cached.replace('/', '--')}"
            if cached_path.is_dir():
                _CACHE_CASE_RESOLUTION_STATS["memo_hits"] += 1
                return cached
            # Stale entry -- drop it and re-scan below.
            _CACHE_CASE_RESOLUTION_MEMO.pop(model_name, None)

    expected_lower = expected_dir.lower()
    try:
        candidates: list[str] = []
        for entry in cache_dir.iterdir():
            if not entry.is_dir():
                continue
            if entry.name.lower() != expected_lower:
                continue
            if not entry.name.startswith("models--"):
                continue
            repo_part = entry.name[len("models--") :]
            if not repo_part:
                continue
            candidates.append(repo_part.replace("--", "/"))

        if candidates:
            # Deterministic tie-break if multiple case variants coexist.
            resolved = sorted(candidates)[0]
            if len(candidates) > 1:
                _CACHE_CASE_RESOLUTION_STATS["tie_breaks"] += 1
            _CACHE_CASE_RESOLUTION_STATS["variant_hits"] += 1
            if use_memo:
                _CACHE_CASE_RESOLUTION_MEMO[model_name] = resolved
            return resolved
    except Exception as exc:
        _CACHE_CASE_RESOLUTION_STATS["errors"] += 1
        logger.debug(f"Could not resolve cached repo_id case for '{model_name}': {exc}")

    _CACHE_CASE_RESOLUTION_STATS["fallbacks"] += 1
    return model_name