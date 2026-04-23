def async_cleanup_stale_devices(
    hass: HomeAssistant,
    entry: InComfortConfigEntry,
    data: InComfortData,
    gateway_device: dr.DeviceEntry,
) -> None:
    """Cleanup stale heater devices and climates."""
    heater_serial_numbers = {heater.serial_no for heater in data.heaters}
    device_registry = dr.async_get(hass)
    device_entries = device_registry.devices.get_devices_for_config_entry_id(
        entry.entry_id
    )
    stale_heater_serial_numbers: list[str] = [
        device_entry.serial_number
        for device_entry in device_entries
        if device_entry.id != gateway_device.id
        and device_entry.serial_number is not None
        and device_entry.serial_number not in heater_serial_numbers
    ]
    if not stale_heater_serial_numbers:
        return
    cleanup_devices: list[str] = []
    # Find stale heater and climate devices
    for serial_number in stale_heater_serial_numbers:
        cleanup_list = [f"{serial_number}_{index}" for index in range(1, 4)]
        cleanup_list.append(serial_number)
        cleanup_identifiers = [{(DOMAIN, cleanup_id)} for cleanup_id in cleanup_list]
        cleanup_devices.extend(
            device_entry.id
            for device_entry in device_entries
            if device_entry.identifiers in cleanup_identifiers
        )
    for device_id in cleanup_devices:
        device_registry.async_remove_device(device_id)