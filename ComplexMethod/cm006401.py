async def list_all_components(
    query: str | None = None,
    component_type: str | None = None,
    fields: list[str] | None = None,
    settings_service: SettingsService | None = None,
) -> list[dict[str, Any]]:
    """Search and retrieve component data with configurable field selection.

    Args:
        query: Optional search term to filter components by name or description.
               Case-insensitive substring matching.
        component_type: Optional component type to filter by (e.g., "agents", "embeddings", "llms").
        fields: List of fields to include in the results. If None, returns all available fields.
               Common fields: name, display_name, description, type, template, documentation,
               icon, is_input, is_output, lazy_loaded, field_order
        settings_service: Settings service instance for loading components.

    Returns:
        List of dictionaries containing the selected fields for each matching component.

    Example:
        >>> # Get all components with default fields
        >>> components = await list_all_components()

        >>> # Get only name and description
        >>> components = await list_all_components(fields=["name", "description"])

        >>> # Search for "openai" components
        >>> components = await list_all_components(
        ...     query="openai",
        ...     fields=["name", "description", "type"]
        ... )

        >>> # Get all LLM components
        >>> components = await list_all_components(
        ...     component_type="llms",
        ...     fields=["name", "display_name"]
        ... )
    """
    if settings_service is None:
        from langflow.services.deps import get_settings_service

        settings_service = get_settings_service()

    try:
        # Get all components from cache
        all_types_dict = await get_and_cache_all_types_dict(settings_service)
        results = []

        # Iterate through component types
        for comp_type, components in all_types_dict.items():
            # Filter by component_type if specified
            if component_type and comp_type.lower() != component_type.lower():
                continue

            # Iterate through components in this type
            for component_name, component_data in components.items():
                # Apply search filter if provided
                if query:
                    name = component_name.lower()
                    display_name = component_data.get("display_name", "").lower()
                    description = component_data.get("description", "").lower()
                    query_lower = query.lower()

                    if query_lower not in name and query_lower not in display_name and query_lower not in description:
                        continue

                # Build result dict with component metadata
                result = {
                    "name": component_name,
                    "type": comp_type,
                }

                # Add all component data fields
                if fields:
                    # Extract only requested fields
                    for field in fields:
                        if field == "name":
                            continue  # Already added
                        if field == "type":
                            continue  # Already added
                        if field in component_data:
                            result[field] = component_data[field]
                else:
                    # Include all fields
                    result.update(component_data)

                results.append(result)

    except Exception as e:  # noqa: BLE001
        await logger.aerror(f"Error listing components: {e}")
        return []
    else:
        return results
    finally:
        await logger.ainfo("Listing components completed")