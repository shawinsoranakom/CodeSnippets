async def async_get_provisioning_entry_from_device_id(
    hass: HomeAssistant, device_id: str
) -> ProvisioningEntry | None:
    """Get provisioning entry from a device ID.

    Raises ValueError if device is invalid
    """
    dev_reg = dr.async_get(hass)

    if not (device_entry := dev_reg.async_get(device_id)):
        raise ValueError(f"Device ID {device_id} is not valid")

    # Use device config entry ID's to validate that this is a valid zwave_js device
    # and to get the client
    config_entry_ids = device_entry.config_entries
    entry: ZwaveJSConfigEntry | None = next(
        (
            entry
            for entry in hass.config_entries.async_entries(DOMAIN)
            if entry.entry_id in config_entry_ids
        ),
        None,
    )
    if entry is None:
        raise ValueError(
            f"Device {device_id} is not from an existing zwave_js config entry"
        )
    if entry.state != ConfigEntryState.LOADED:
        raise ValueError(f"Device {device_id} config entry is not loaded")

    client = entry.runtime_data.client
    driver = client.driver

    if driver is None:
        raise ValueError("Driver is not ready.")

    provisioning_entries = await driver.controller.async_get_provisioning_entries()
    for provisioning_entry in provisioning_entries:
        if (
            provisioning_entry.additional_properties
            and provisioning_entry.additional_properties.get("device_id") == device_id
        ):
            return provisioning_entry

    return None