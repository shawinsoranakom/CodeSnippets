async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: UnifiConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    hub = config_entry.runtime_data
    diag: dict[str, Any] = {}
    macs_to_redact: dict[str, str] = {}

    counter = 0
    for mac in chain(hub.api.clients, hub.api.devices):
        macs_to_redact[mac] = format_mac(str(counter).zfill(12))
        counter += 1

    for device in hub.api.devices.values():
        for entry in device.raw.get("ethernet_table", []):
            mac = entry.get("mac", "")
            if mac not in macs_to_redact:
                macs_to_redact[mac] = format_mac(str(counter).zfill(12))
                counter += 1

    diag["config"] = async_redact_data(
        async_replace_dict_data(config_entry.as_dict(), macs_to_redact), REDACT_CONFIG
    )
    diag["role_is_admin"] = hub.is_admin
    diag["clients"] = {
        macs_to_redact[k]: async_redact_data(
            async_replace_dict_data(v.raw, macs_to_redact), REDACT_CLIENTS
        )
        for k, v in hub.api.clients.items()
    }
    diag["devices"] = {
        macs_to_redact[k]: async_redact_data(
            async_replace_dict_data(v.raw, macs_to_redact), REDACT_DEVICES
        )
        for k, v in hub.api.devices.items()
    }
    diag["dpi_apps"] = {k: v.raw for k, v in hub.api.dpi_apps.items()}
    diag["dpi_groups"] = {k: v.raw for k, v in hub.api.dpi_groups.items()}
    diag["wlans"] = {
        k: async_redact_data(
            async_replace_dict_data(v.raw, macs_to_redact), REDACT_WLANS
        )
        for k, v in hub.api.wlans.items()
    }

    return diag