async def async_setup_entry(
    hass: HomeAssistant,
    entry: AirzoneCloudConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add Airzone Cloud select from a config_entry."""
    coordinator = entry.runtime_data

    # Zones
    entities: list[AirzoneZoneSelect] = [
        AirzoneZoneSelect(
            coordinator,
            description,
            zone_id,
            zone_data,
        )
        for description in MAIN_ZONE_SELECT_TYPES
        for zone_id, zone_data in coordinator.data.get(AZD_ZONES, {}).items()
        if description.key in zone_data and zone_data.get(AZD_MASTER)
    ]

    entities.extend(
        AirzoneZoneSelect(
            coordinator,
            description,
            zone_id,
            zone_data,
        )
        for description in ZONE_SELECT_TYPES
        for zone_id, zone_data in coordinator.data.get(AZD_ZONES, {}).items()
        if description.key in zone_data
    )

    async_add_entities(entities)