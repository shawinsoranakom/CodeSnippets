async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: RoborockConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Roborock select platform."""

    async_add_entities(
        RoborockSelectEntity(coordinator, description, options)
        for coordinator in config_entry.runtime_data.v1
        for description in SELECT_DESCRIPTIONS
        if (
            (options := description.options_lambda(coordinator.properties_api))
            is not None
        )
    )
    async_add_entities(
        RoborockCurrentMapSelectEntity(
            f"selected_map_{coordinator.duid_slug}", coordinator, home_trait, map_trait
        )
        for coordinator in config_entry.runtime_data.v1
        if (home_trait := coordinator.properties_api.home) is not None
        if (map_trait := coordinator.properties_api.maps) is not None
    )
    async_add_entities(
        RoborockB01SelectEntity(coordinator, description, options)
        for coordinator in config_entry.runtime_data.b01_q7
        for description in B01_SELECT_DESCRIPTIONS
        if (options := description.options_lambda(coordinator.api)) is not None
    )
    async_add_entities(
        RoborockSelectEntityA01(coordinator, description)
        for coordinator in config_entry.runtime_data.a01
        for description in A01_SELECT_DESCRIPTIONS
        if description.data_protocol in coordinator.request_protocols
    )
    async_add_entities(
        RoborockQ10CleanModeSelectEntity(coordinator)
        for coordinator in config_entry.runtime_data.b01_q10
    )