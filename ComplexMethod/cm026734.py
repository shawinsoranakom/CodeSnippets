async def websocket_remove_config_entry_from_device(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Remove config entry from a device."""
    registry = dr.async_get(hass)
    config_entry_id = msg["config_entry_id"]
    device_id = msg["device_id"]

    if (config_entry := hass.config_entries.async_get_entry(config_entry_id)) is None:
        raise HomeAssistantError("Unknown config entry")

    if not config_entry.supports_remove_device:
        raise HomeAssistantError("Config entry does not support device removal")

    if (device_entry := registry.async_get(device_id)) is None:
        raise HomeAssistantError("Unknown device")

    if config_entry_id not in device_entry.config_entries:
        raise HomeAssistantError("Config entry not in device")

    try:
        integration = await loader.async_get_integration(hass, config_entry.domain)
        component = await integration.async_get_component()
    except (ImportError, loader.IntegrationNotFound) as exc:
        raise HomeAssistantError("Integration not found") from exc

    if not await component.async_remove_config_entry_device(
        hass, config_entry, device_entry
    ):
        raise HomeAssistantError(
            "Failed to remove device entry, rejected by integration"
        )

    # Integration might have removed the config entry already, that is fine.
    if registry.async_get(device_id):
        entry = registry.async_update_device(
            device_id, remove_config_entry_id=config_entry_id
        )

        entry_as_dict = entry.dict_repr if entry else None
    else:
        entry_as_dict = None

    connection.send_message(websocket_api.result_message(msg["id"], entry_as_dict))