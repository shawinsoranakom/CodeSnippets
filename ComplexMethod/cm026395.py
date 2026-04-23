async def async_setup_entry(
    hass: HomeAssistant,
    entry: HikvisionConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Hikvision binary sensors from a config entry."""
    data = entry.runtime_data
    camera = data.camera

    sensors = camera.current_event_states
    if sensors is None or not sensors:
        _LOGGER.warning(
            "Hikvision %s %s has no sensors available. "
            "Ensure event detection is enabled and configured on the device",
            data.device_type,
            data.device_name,
        )
        return

    # Log warnings for unknown sensor types and skip them
    for sensor_type in sensors:
        if sensor_type not in BINARY_SENSOR_DESCRIPTIONS:
            _LOGGER.warning(
                "Unknown Hikvision sensor type '%s', please report this at "
                "https://github.com/home-assistant/core/issues",
                sensor_type,
            )

    async_add_entities(
        HikvisionBinarySensor(
            entry=entry,
            description=BINARY_SENSOR_DESCRIPTIONS[sensor_type],
            sensor_type=sensor_type,
            channel=channel_info[1],
        )
        for sensor_type, channel_list in sensors.items()
        if sensor_type in BINARY_SENSOR_DESCRIPTIONS
        for channel_info in channel_list
    )