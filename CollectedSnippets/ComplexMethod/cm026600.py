async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: BoschAlarmConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up binary sensors for alarm points and the connection status."""
    panel = config_entry.runtime_data

    entities: list[BinarySensorEntity] = [
        PointSensor(panel, point_id, config_entry.unique_id or config_entry.entry_id)
        for point_id in panel.points
    ]

    entities.extend(
        PanelFaultsSensor(
            panel,
            config_entry.unique_id or config_entry.entry_id,
            fault_type,
        )
        for fault_type in FAULT_TYPES
    )

    entities.extend(
        AreaReadyToArmSensor(
            panel, area_id, config_entry.unique_id or config_entry.entry_id, "away"
        )
        for area_id in panel.areas
    )

    entities.extend(
        AreaReadyToArmSensor(
            panel, area_id, config_entry.unique_id or config_entry.entry_id, "home"
        )
        for area_id in panel.areas
    )

    async_add_entities(entities)