async def async_setup_entry(
    _hass: HomeAssistant,
    entry: MelCloudConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up MELCloud device sensors based on config_entry."""
    coordinators = entry.runtime_data

    entities: list[MelDeviceSensor] = [
        MelDeviceSensor(coordinator, description)
        for description in ATA_SENSORS
        for coordinator in coordinators.get(DEVICE_TYPE_ATA, [])
        if description.enabled(coordinator)
    ] + [
        MelDeviceSensor(coordinator, description)
        for description in ATW_SENSORS
        for coordinator in coordinators.get(DEVICE_TYPE_ATW, [])
        if description.enabled(coordinator)
    ]
    entities.extend(
        [
            AtwZoneSensor(coordinator, zone, description)
            for coordinator in coordinators.get(DEVICE_TYPE_ATW, [])
            for zone in coordinator.device.zones
            for description in ATW_ZONE_SENSORS
            if description.enabled(zone)
        ]
    )
    async_add_entities(entities)