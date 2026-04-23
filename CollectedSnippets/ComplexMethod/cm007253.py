async def ensure_component_loaded(component_type: str, component_name: str, settings_service: "SettingsService"):
    """Ensure a component is fully loaded if it was only partially loaded."""
    # If already fully loaded, return immediately
    component_key = f"{component_type}:{component_name}"
    if component_key in component_cache.fully_loaded_components:
        return

    # If we don't have a cache or the component doesn't exist in the cache, nothing to do
    if (
        not component_cache.all_types_dict
        or "components" not in component_cache.all_types_dict
        or component_type not in component_cache.all_types_dict["components"]
        or component_name not in component_cache.all_types_dict["components"][component_type]
    ):
        return

    # Check if component is marked for lazy loading
    if component_cache.all_types_dict["components"][component_type][component_name].get("lazy_loaded", False):
        await logger.adebug(f"Fully loading component {component_type}:{component_name}")

        # Load just this specific component
        full_component = await load_single_component(
            component_type, component_name, settings_service.settings.components_path
        )

        if full_component:
            # Replace the stub with the fully loaded component
            component_cache.all_types_dict["components"][component_type][component_name] = full_component
            # Remove lazy_loaded flag if it exists
            if "lazy_loaded" in component_cache.all_types_dict["components"][component_type][component_name]:
                del component_cache.all_types_dict["components"][component_type][component_name]["lazy_loaded"]

            # Mark as fully loaded
            component_cache.fully_loaded_components[component_key] = True
            await logger.adebug(f"Component {component_type}:{component_name} fully loaded")
        else:
            await logger.awarning(f"Failed to fully load component {component_type}:{component_name}")