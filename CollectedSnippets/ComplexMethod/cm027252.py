async def async_update_device(
    hass: HomeAssistant,
    entry: ConfigEntry,
    adapter: str,
    details: AdapterDetails,
    via_device_id: str | None = None,
) -> None:
    """Update device registry entry.

    The physical adapter can change from hci0/hci1 on reboot
    or if the user moves around the usb sticks so we need to
    update the device with the new location so they can
    figure out where the adapter is.
    """
    address = details[ADAPTER_ADDRESS]
    connections = {(dr.CONNECTION_BLUETOOTH, address)}
    device_registry = dr.async_get(hass)
    # We only have one device for the config entry
    # so if the address has been corrected, make
    # sure the device entry reflects the correct
    # address
    for device in dr.async_entries_for_config_entry(device_registry, entry.entry_id):
        for conn_type, conn_value in device.connections:
            if conn_type == dr.CONNECTION_BLUETOOTH and conn_value != address:
                device_registry.async_update_device(
                    device.id, new_connections=connections
                )
                break
    device_entry = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        name=adapter_human_name(adapter, address),
        connections=connections,
        manufacturer=details[ADAPTER_MANUFACTURER],
        model=adapter_model(details),
        sw_version=details.get(ADAPTER_SW_VERSION),
        hw_version=details.get(ADAPTER_HW_VERSION),
    )
    if via_device_id and (via_device_entry := device_registry.async_get(via_device_id)):
        kwargs: dict[str, Any] = {"via_device_id": via_device_id}
        if not device_entry.area_id and via_device_entry.area_id:
            kwargs["area_id"] = via_device_entry.area_id
        device_registry.async_update_device(device_entry.id, **kwargs)