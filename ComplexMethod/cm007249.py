async def _load_from_index_or_cache(
    settings_service: Optional["SettingsService"] = None,
) -> tuple[dict[str, Any], str | None]:
    """Load components from prebuilt index or cache.

    Args:
        settings_service: Optional settings service to get custom index path

    Returns:
        Tuple of (modules_dict, index_source) where index_source is "builtin", "cache", or None if failed
    """
    modules_dict: dict[str, Any] = {}

    # Try to load from prebuilt index first
    custom_index_path = None
    if settings_service and settings_service.settings.components_index_path:
        custom_index_path = settings_service.settings.components_index_path
        await logger.adebug(f"Using custom component index: {custom_index_path}")

    index = _read_component_index(custom_index_path)
    if index and "entries" in index:
        source = custom_index_path or "built-in index"
        await logger.adebug(f"Loading components from {source}")
        # Reconstruct modules_dict from index entries
        for top_level, components in index["entries"]:
            if top_level not in modules_dict:
                modules_dict[top_level] = {}
            modules_dict[top_level].update(components)
        # Filter disabled components for Astra cloud
        modules_dict = filter_disabled_components_from_dict(modules_dict)
        await logger.adebug(f"Loaded {len(modules_dict)} component categories from index")
        return modules_dict, "builtin"

    # Index failed to load - try cache
    await logger.adebug("Prebuilt index not available, checking cache")
    try:
        cache_path = _get_cache_path()
    except Exception as e:  # noqa: BLE001
        await logger.adebug(f"Cache load failed: {e}")
    else:
        if cache_path.exists():
            await logger.adebug(f"Attempting to load from cache: {cache_path}")
            index = _read_component_index(str(cache_path))
            if index and "entries" in index:
                await logger.adebug("Loading components from cached index")
                for top_level, components in index["entries"]:
                    if top_level not in modules_dict:
                        modules_dict[top_level] = {}
                    modules_dict[top_level].update(components)
                # Filter disabled components for Astra cloud
                modules_dict = filter_disabled_components_from_dict(modules_dict)
                await logger.adebug(f"Loaded {len(modules_dict)} component categories from cache")
                return modules_dict, "cache"

    return modules_dict, None