def shrink_profile(
    profile_path: str,
    level: ShrinkLevel = ShrinkLevel.AGGRESSIVE,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Shrink a Chrome profile to reduce storage while preserving auth data.

    Args:
        profile_path: Path to profile directory
        level: How aggressively to shrink (LIGHT/MEDIUM/AGGRESSIVE/MINIMAL)
        dry_run: If True, only report what would be removed

    Returns:
        Dict with 'removed', 'kept', 'bytes_freed', 'size_before', 'size_after', 'errors'
    """
    if level == ShrinkLevel.NONE:
        return {"removed": [], "kept": [], "bytes_freed": 0, "errors": []}

    profile = Path(profile_path)
    if not profile.exists() or not profile.is_dir():
        raise ValueError(f"Profile not found: {profile_path}")

    # Chrome profiles may have data in Default/ subdirectory
    target = profile / "Default" if (profile / "Default").is_dir() else profile

    keep = KEEP_PATTERNS[level]
    result = {"removed": [], "kept": [], "bytes_freed": 0, "errors": [], "size_before": _get_size(profile)}

    for item in target.iterdir():
        name = item.name
        # Check if item matches any keep pattern
        if any(name == p or name.startswith(p) for p in keep):
            result["kept"].append(name)
        else:
            size = _get_size(item)
            if not dry_run:
                try:
                    shutil.rmtree(item) if item.is_dir() else item.unlink()
                    result["removed"].append(name)
                    result["bytes_freed"] += size
                except Exception as e:
                    result["errors"].append(f"{name}: {e}")
            else:
                result["removed"].append(name)
                result["bytes_freed"] += size

    result["size_after"] = _get_size(profile) if not dry_run else None
    return result