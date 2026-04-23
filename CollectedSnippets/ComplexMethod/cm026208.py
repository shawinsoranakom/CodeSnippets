async def async_reconnect_client(hass: HomeAssistant, data: Mapping[str, Any]) -> None:
    """Try to get wireless client to reconnect to Wi-Fi."""
    device_registry = dr.async_get(hass)
    device_entry = device_registry.async_get(data[ATTR_DEVICE_ID])

    if device_entry is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="reconnect_client_device_not_found",
        )

    mac = ""
    for connection in device_entry.connections:
        if connection[0] == CONNECTION_NETWORK_MAC:
            mac = connection[1]
            break

    if mac == "":
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="reconnect_client_no_mac",
        )

    for config_entry in hass.config_entries.async_loaded_entries(DOMAIN):
        if (
            (not (hub := config_entry.runtime_data).available)
            or (client := hub.api.clients.get(mac)) is None
            or client.is_wired
        ):
            continue

        try:
            await hub.api.request(ClientReconnectRequest.create(mac))
        except aiounifi.AiounifiException as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="reconnect_client_request_failed",
            ) from err