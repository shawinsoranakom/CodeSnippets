async def async_setup_entry(
    hass: HomeAssistant,
    entry: AirzoneCloudConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add Airzone Cloud sensors from a config_entry."""
    coordinator = entry.runtime_data

    # Aidoos
    sensors: list[AirzoneSensor] = [
        AirzoneAidooSensor(
            coordinator,
            description,
            aidoo_id,
            aidoo_data,
        )
        for aidoo_id, aidoo_data in coordinator.data.get(AZD_AIDOOS, {}).items()
        for description in AIDOO_SENSOR_TYPES
        if description.key in aidoo_data
    ]

    # WebServers
    sensors.extend(
        AirzoneWebServerSensor(
            coordinator,
            description,
            ws_id,
            ws_data,
        )
        for ws_id, ws_data in coordinator.data.get(AZD_WEBSERVERS, {}).items()
        for description in WEBSERVER_SENSOR_TYPES
        if description.key in ws_data
    )

    # Zones
    sensors.extend(
        AirzoneZoneSensor(
            coordinator,
            description,
            zone_id,
            zone_data,
        )
        for zone_id, zone_data in coordinator.data.get(AZD_ZONES, {}).items()
        for description in ZONE_SENSOR_TYPES
        if description.key in zone_data
    )

    async_add_entities(sensors)