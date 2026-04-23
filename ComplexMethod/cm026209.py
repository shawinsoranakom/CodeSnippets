async def async_remove_clients(hass: HomeAssistant, data: Mapping[str, Any]) -> None:
    """Remove select clients from UniFi Network.

    Validates based on:
    - Total time between first seen and last seen is less than 15 minutes.
    - Neither IP, hostname nor name is configured.
    """
    for config_entry in hass.config_entries.async_loaded_entries(DOMAIN):
        if not (hub := config_entry.runtime_data).available:
            continue

        clients_to_remove = []

        for client in hub.api.clients_all.values():
            if (
                client.last_seen
                and client.first_seen
                and client.last_seen - client.first_seen > 900
            ):
                continue

            if any({client.fixed_ip, client.hostname, client.name}):
                continue

            clients_to_remove.append(client.mac)

        if clients_to_remove:
            try:
                await hub.api.request(ClientRemoveRequest.create(clients_to_remove))
            except aiounifi.AiounifiException as err:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="remove_clients_request_failed",
                ) from err