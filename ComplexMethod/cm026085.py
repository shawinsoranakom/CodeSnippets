async def async_setup_entry(
    hass: HomeAssistant,
    entry: DevoloHomeControlConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Get all binary sensor and multi level sensor devices and setup them via config entry."""
    entities: list[BinarySensorEntity] = []

    for gateway in entry.runtime_data:
        entities.extend(
            DevoloBinaryDeviceEntity(
                homecontrol=gateway,
                device_instance=device,
                element_uid=binary_sensor,
            )
            for device in gateway.binary_sensor_devices
            for binary_sensor in device.binary_sensor_property
        )
        entities.extend(
            DevoloRemoteControl(
                homecontrol=gateway,
                device_instance=device,
                element_uid=remote,
                key=index,
            )
            for device in gateway.devices.values()
            if hasattr(device, "remote_control_property")
            for remote in device.remote_control_property
            for index in range(1, device.remote_control_property[remote].key_count + 1)
        )
    async_add_entities(entities)