async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: DeconzConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    hub = config_entry.runtime_data
    diag: dict[str, Any] = {}

    diag["config"] = async_redact_data(config_entry.as_dict(), REDACT_CONFIG)
    diag["deconz_config"] = async_redact_data(hub.api.config.raw, REDACT_DECONZ_CONFIG)
    diag["websocket_state"] = (
        hub.api.websocket.state.value if hub.api.websocket else "Unknown"
    )
    diag["deconz_ids"] = hub.deconz_ids
    diag["entities"] = hub.entities
    diag["events"] = {
        event.serial: {
            "event_id": event.event_id,
            "event_type": type(event).__name__,
        }
        for event in hub.events
    }
    diag["alarm_systems"] = {k: v.raw for k, v in hub.api.alarm_systems.items()}
    diag["groups"] = {k: v.raw for k, v in hub.api.groups.items()}
    diag["lights"] = {k: v.raw for k, v in hub.api.lights.items()}
    diag["scenes"] = {k: v.raw for k, v in hub.api.scenes.items()}
    diag["sensors"] = {k: v.raw for k, v in hub.api.sensors.items()}

    return diag