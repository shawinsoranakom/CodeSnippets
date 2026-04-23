def _async_get_system_for_service_call(
    hass: HomeAssistant, call: ServiceCall
) -> SystemType:
    """Get the SimpliSafe system related to a service call (by device ID)."""
    device_id = call.data[ATTR_DEVICE_ID]
    device_registry = dr.async_get(hass)

    if (
        alarm_control_panel_device_entry := device_registry.async_get(device_id)
    ) is None:
        raise vol.Invalid("Invalid device ID specified")

    assert alarm_control_panel_device_entry.via_device_id

    if (
        base_station_device_entry := device_registry.async_get(
            alarm_control_panel_device_entry.via_device_id
        )
    ) is None:
        raise ValueError("No base station registered for alarm control panel")

    [system_id_str] = [
        identity[1]
        for identity in base_station_device_entry.identifiers
        if identity[0] == DOMAIN
    ]
    system_id = int(system_id_str)

    entry: SimpliSafeConfigEntry | None
    for entry_id in base_station_device_entry.config_entries:
        if (
            (entry := hass.config_entries.async_get_entry(entry_id)) is None
            or entry.domain != DOMAIN
            or entry.state != ConfigEntryState.LOADED
        ):
            continue
        return entry.runtime_data.systems[system_id]

    raise ValueError(f"No system for device ID: {device_id}")