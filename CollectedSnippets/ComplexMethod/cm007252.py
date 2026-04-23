async def _determine_loading_strategy(settings_service: "SettingsService") -> dict[str, Any]:
    """Determines and executes the appropriate component loading strategy.

    Args:
        settings_service: Service containing loading configuration

    Returns:
        Dictionary containing loaded component types and templates
    """
    component_cache.all_types_dict = {}
    if settings_service.settings.lazy_load_components:
        # Partial loading mode - just load component metadata
        await logger.adebug("Using partial component loading")
        component_cache.all_types_dict = await aget_component_metadata(settings_service.settings.components_path)
    elif settings_service.settings.components_path:
        # Traditional full loading - filter out base components path to only load custom components
        custom_paths = [p for p in settings_service.settings.components_path if p != BASE_COMPONENTS_PATH]
        if custom_paths:
            component_cache.all_types_dict = await aget_all_types_dict(custom_paths)

    # Log custom component loading stats
    components_dict = component_cache.all_types_dict or {}
    component_count = sum(len(comps) for comps in components_dict.get("components", {}).values())
    if component_count > 0 and settings_service.settings.components_path:
        await logger.adebug(
            f"Built {component_count} custom components from {settings_service.settings.components_path}"
        )

    return component_cache.all_types_dict or {}