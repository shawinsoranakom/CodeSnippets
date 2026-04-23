async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: WattsVisionConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    runtime_data = entry.runtime_data
    hub_coordinator = runtime_data.hub_coordinator
    device_coordinators = runtime_data.device_coordinators
    now = datetime.now()

    return async_redact_data(
        {
            "entry": entry.as_dict(),
            "hub_coordinator": {
                "last_update_success": hub_coordinator.last_update_success,
                "last_exception": (
                    str(hub_coordinator.last_exception)
                    if hub_coordinator.last_exception
                    else None
                ),
                "last_discovery": (
                    hub_coordinator.last_discovery.isoformat()
                    if hub_coordinator.last_discovery
                    else None
                ),
                "total_devices": len(hub_coordinator.data),
                "supported_devices": len(device_coordinators),
            },
            "hub_data": {
                device_id: dataclasses.asdict(device)
                for device_id, device in hub_coordinator.data.items()
            },
            "devices": {
                device_id: {
                    "device": dataclasses.asdict(coordinator.data.device),
                    "last_update_success": coordinator.last_update_success,
                    "fast_polling_active": (
                        coordinator.fast_polling_until is not None
                        and coordinator.fast_polling_until > now
                    ),
                    "fast_polling_until": (
                        coordinator.fast_polling_until.isoformat()
                        if coordinator.fast_polling_until is not None
                        and coordinator.fast_polling_until > now
                        else None
                    ),
                }
                for device_id, coordinator in device_coordinators.items()
            },
        },
        {CONF_ACCESS_TOKEN, *TO_REDACT},
    )