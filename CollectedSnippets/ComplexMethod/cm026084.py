async def async_setup_entry(
    hass: HomeAssistant,
    entry: DevoloHomeControlConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Get all sensor devices and setup them via config entry."""
    entities: list[SensorEntity] = []

    for gateway in entry.runtime_data:
        entities.extend(
            DevoloGenericMultiLevelDeviceEntity(
                homecontrol=gateway,
                device_instance=device,
                element_uid=multi_level_sensor,
            )
            for device in gateway.multi_level_sensor_devices
            for multi_level_sensor in device.multi_level_sensor_property
        )
        entities.extend(
            DevoloConsumptionEntity(
                homecontrol=gateway,
                device_instance=device,
                element_uid=consumption,
                consumption=consumption_type,
            )
            for device in gateway.devices.values()
            if hasattr(device, "consumption_property")
            for consumption in device.consumption_property
            for consumption_type in ("current", "total")
        )
        entities.extend(
            DevoloBatteryEntity(
                homecontrol=gateway,
                device_instance=device,
                element_uid=f"devolo.BatterySensor:{device.uid}",
            )
            for device in gateway.devices.values()
            if hasattr(device, "battery_level")
        )

    async_add_entities(entities)