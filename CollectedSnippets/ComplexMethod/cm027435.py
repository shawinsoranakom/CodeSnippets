async def async_setup_entry(
    hass: HomeAssistant,
    entry: FreeboxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensors."""
    router = entry.runtime_data

    _LOGGER.debug(
        "%s - %s - %s temperature sensors",
        router.name,
        router.mac,
        len(router.sensors_temperature),
    )
    entities: list[SensorEntity] = [
        FreeboxSensor(
            router,
            SensorEntityDescription(
                key=sensor_name,
                name=f"Freebox {sensor_name}",
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
        )
        for sensor_name in router.sensors_temperature
    ]

    entities.extend(
        [FreeboxSensor(router, description) for description in CONNECTION_SENSORS]
    )
    entities.extend(
        [FreeboxCallSensor(router, description) for description in CALL_SENSORS]
    )

    _LOGGER.debug("%s - %s - %s disk(s)", router.name, router.mac, len(router.disks))
    entities.extend(
        FreeboxDiskSensor(router, disk, partition, description)
        for disk in router.disks.values()
        for partition in disk["partitions"].values()
        for description in DISK_PARTITION_SENSORS
    )

    entities.extend(
        FreeboxBatterySensor(router, node, endpoint)
        for node in router.home_devices.values()
        for endpoint in node["show_endpoints"]
        if (
            endpoint["name"] == "battery"
            and endpoint["ep_type"] == "signal"
            and endpoint.get("value") is not None
        )
    )

    if entities:
        async_add_entities(entities, True)