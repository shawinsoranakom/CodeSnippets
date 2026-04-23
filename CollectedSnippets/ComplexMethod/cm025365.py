async def async_setup_entry(
    hass: HomeAssistant,
    entry: SimpliSafeConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up SimpliSafe binary sensors based on a config entry."""
    simplisafe = entry.runtime_data

    sensors: list[BatteryBinarySensor | TriggeredBinarySensor] = []

    for system in simplisafe.systems.values():
        if system.version == 2:
            LOGGER.warning("Skipping sensor setup for V2 system: %s", system.system_id)
            continue

        if TYPE_CHECKING:
            assert isinstance(system, SystemV3)
        for sensor in system.sensors.values():
            if sensor.type in TRIGGERED_SENSOR_TYPES:
                sensors.append(
                    TriggeredBinarySensor(
                        simplisafe,
                        system,
                        cast(SensorV3, sensor),
                        TRIGGERED_SENSOR_TYPES[sensor.type],
                    )
                )
            if sensor.type in SUPPORTED_BATTERY_SENSOR_TYPES:
                sensors.append(
                    BatteryBinarySensor(simplisafe, system, cast(DeviceV3, sensor))
                )

        sensors.extend(
            BatteryBinarySensor(simplisafe, system, lock)
            for lock in system.locks.values()
        )

    async_add_entities(sensors)