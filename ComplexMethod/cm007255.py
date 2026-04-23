async def get_type_dict(component_type: str, settings_service: Optional["SettingsService"] = None):
    """Get a specific component type dictionary, loading if needed."""
    if settings_service is None:
        # Import here to avoid circular imports
        from langflow.services.deps import get_settings_service

        settings_service = get_settings_service()

    # Make sure all_types_dict is loaded (at least partially)
    if component_cache.all_types_dict is None:
        await get_and_cache_all_types_dict(settings_service)

    # Check if component type exists in the cache
    if (
        component_cache.all_types_dict
        and "components" in component_cache.all_types_dict
        and component_type in component_cache.all_types_dict["components"]
    ):
        # If in lazy mode, ensure all components of this type are fully loaded
        if settings_service.settings.lazy_load_components:
            for component_name in list(component_cache.all_types_dict["components"][component_type].keys()):
                await ensure_component_loaded(component_type, component_name, settings_service)

        return component_cache.all_types_dict["components"][component_type]

    return {}