async def async_setup_entry(
    hass: HomeAssistant,
    entry: SwitchbotConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Switchbot sensor based on a config entry."""
    coordinator = entry.runtime_data
    parsed_data = coordinator.device.parsed_data
    sensor_entities: list[SensorEntity] = []
    if isinstance(coordinator.device, switchbot.SwitchbotRelaySwitch2PM):
        sensor_entities.extend(
            SwitchBotSensor(coordinator, sensor, channel)
            for channel in range(1, coordinator.device.channel + 1)
            for sensor in coordinator.device.get_parsed_data(channel)
            if sensor in SENSOR_TYPES
        )
    elif coordinator.model == SwitchbotModel.PRESENCE_SENSOR:
        sensor_entities.extend(
            SwitchBotSensor(coordinator, sensor)
            for sensor in (
                *(
                    s
                    for s in parsed_data
                    if s in SENSOR_TYPES and s not in ("battery", "battery_range")
                ),
                "battery_range",
            )
        )
        if "battery" in parsed_data:
            sensor_entities.append(SwitchBotSensor(coordinator, "battery"))
    else:
        sensors: set[str] = {sensor for sensor in parsed_data if sensor in SENSOR_TYPES}
        if (
            isinstance(coordinator.device, switchbot.SwitchbotAirPurifier)
            and coordinator.model in AIRPURIFIER_PM25_MODELS
        ):
            sensors.add("pm25")
        sensor_entities.extend(
            SwitchBotSensor(coordinator, sensor) for sensor in sensors
        )
    sensor_entities.append(SwitchbotRSSISensor(coordinator, "rssi"))
    async_add_entities(sensor_entities)