def _is_cache_valid(
    cache_path: pathlib.Path,
    ttl_hours: int,
    validate_lastmod: bool,
    current_lastmod: Optional[str] = None
) -> bool:
    """
    Check if sitemap cache is still valid.

    Returns False (invalid) if:
    - File doesn't exist
    - File is corrupted/unreadable
    - TTL expired (if ttl_hours > 0)
    - Sitemap lastmod is newer than cache (if validate_lastmod=True)
    """
    if not cache_path.exists():
        return False

    try:
        with open(cache_path, "r") as f:
            data = json.load(f)

        # Check version
        if data.get("version") != 1:
            return False

        # Check TTL
        if ttl_hours > 0:
            created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            age_hours = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600
            if age_hours > ttl_hours:
                return False

        # Check lastmod
        if validate_lastmod and current_lastmod:
            cached_lastmod = data.get("sitemap_lastmod")
            if cached_lastmod and current_lastmod > cached_lastmod:
                return False

        # Check URL count (sanity check - if 0, likely corrupted)
        if data.get("url_count", 0) == 0:
            return False

        return True

    except (json.JSONDecodeError, KeyError, ValueError, IOError):
        # Corrupted cache - return False to trigger refetch
        return False