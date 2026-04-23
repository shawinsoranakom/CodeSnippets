async def get_component_by_name(
    component_name: str,
    component_type: str | None = None,
    fields: list[str] | None = None,
    settings_service: SettingsService | None = None,
) -> dict[str, Any] | None:
    """Get a specific component by its name.

    Args:
        component_name: The name of the component to retrieve.
        component_type: Optional component type to narrow search.
        fields: Optional list of fields to include. If None, returns all fields.
        settings_service: Settings service instance for loading components.

    Returns:
        Dictionary containing the component data with selected fields, or None if not found.

    Example:
        >>> component = await get_component_by_name(
        ...     "OpenAIModel",
        ...     fields=["display_name", "description", "template"]
        ... )
    """
    if settings_service is None:
        from langflow.services.deps import get_settings_service

        settings_service = get_settings_service()

    try:
        all_types_dict = await get_and_cache_all_types_dict(settings_service)

        # If component_type specified, search only that type
        if component_type:
            components = all_types_dict.get(component_type, {})
            component_data = components.get(component_name)

            if component_data:
                result = {"name": component_name, "type": component_type}
                if fields:
                    for field in fields:
                        if field in {"name", "type"}:
                            continue
                        if field in component_data:
                            result[field] = component_data[field]
                else:
                    result.update(component_data)
                return result
        else:
            # Search across all types
            for comp_type, components in all_types_dict.items():
                if component_name in components:
                    component_data = components[component_name]
                    result = {"name": component_name, "type": comp_type}
                    if fields:
                        for field in fields:
                            if field in {"name", "type"}:
                                continue
                            if field in component_data:
                                result[field] = component_data[field]
                    else:
                        result.update(component_data)
                    return result

    except Exception as e:  # noqa: BLE001
        await logger.aerror(f"Error getting component {component_name}: {e}")
        return None
    else:
        return None
    finally:
        await logger.ainfo("Getting component completed")