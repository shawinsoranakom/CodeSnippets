def async_get_node_from_device_id(
    hass: HomeAssistant, device_id: str, dev_reg: dr.DeviceRegistry | None = None
) -> ZwaveNode:
    """Get node from a device ID.

    Raises ValueError if device is invalid or node can't be found.
    """
    if not dev_reg:
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

    # Get node ID from device identifier, perform some validation, and then get the
    # node
    identifiers = get_home_and_node_id_from_device_entry(device_entry)

    node_id = identifiers[1] if identifiers else None

    if node_id is None or node_id not in driver.controller.nodes:
        raise ValueError(f"Node for device {device_id} can't be found")

    return driver.controller.nodes[node_id]