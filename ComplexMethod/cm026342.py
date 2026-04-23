async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: OmadaConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    controller = entry.runtime_data

    devices = controller.devices_coordinator.data
    clients = controller.clients_coordinator.data

    gateway_data: dict[str, Any] | None = None
    if (
        gateway_coordinator := controller.gateway_coordinator
    ) and gateway_coordinator.data:
        gateway = next(iter(gateway_coordinator.data.values()))
        gateway_data = gateway.raw_data

    mac_values = set(devices) | set(clients)
    for client in clients.values():
        if ap_mac := client.raw_data.get("apMac"):
            mac_values.add(ap_mac)
    if gateway_data and (gateway_mac := gateway_data.get("mac")):
        mac_values.add(gateway_mac)

    replacements = _build_identifier_replacements(mac_values)

    return {
        "entry": async_redact_data(entry.as_dict(), ENTRY_TO_REDACT),
        "runtime": {
            "devices": {
                replacements[mac]: _redact_runtime_record(
                    device.raw_data,
                    replacements,
                )
                for mac, device in devices.items()
            },
            "clients": {
                replacements[mac]: _redact_runtime_record(
                    client.raw_data,
                    replacements,
                )
                for mac, client in clients.items()
            },
            "gateway": (
                _redact_runtime_record(gateway_data, replacements)
                if gateway_data is not None
                else None
            ),
        },
    }