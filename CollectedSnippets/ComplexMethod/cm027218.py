async def async_setup_entry(
    hass: HomeAssistant,
    entry: AirzoneCloudConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add Airzone Cloud binary sensors from a config_entry."""
    coordinator = entry.runtime_data

    binary_sensors: list[AirzoneBinarySensor] = [
        AirzoneAidooBinarySensor(
            coordinator,
            description,
            aidoo_id,
            aidoo_data,
        )
        for aidoo_id, aidoo_data in coordinator.data.get(AZD_AIDOOS, {}).items()
        for description in AIDOO_BINARY_SENSOR_TYPES
        if description.key in aidoo_data
    ]

    binary_sensors.extend(
        AirzoneSystemBinarySensor(
            coordinator,
            description,
            system_id,
            system_data,
        )
        for system_id, system_data in coordinator.data.get(AZD_SYSTEMS, {}).items()
        for description in SYSTEM_BINARY_SENSOR_TYPES
        if description.key in system_data
    )

    binary_sensors.extend(
        AirzoneZoneBinarySensor(
            coordinator,
            description,
            zone_id,
            zone_data,
        )
        for zone_id, zone_data in coordinator.data.get(AZD_ZONES, {}).items()
        for description in ZONE_BINARY_SENSOR_TYPES
        if description.key in zone_data
    )

    async_add_entities(binary_sensors)