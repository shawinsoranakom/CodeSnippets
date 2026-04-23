def get_plex_server(
    hass: HomeAssistant,
    plex_server_name: str | None = None,
    plex_server_id: str | None = None,
) -> PlexServer:
    """Retrieve a configured Plex server by name."""
    if DOMAIN not in hass.data:
        raise HomeAssistantError("Plex integration not configured")
    servers: dict[str, PlexServer] = get_plex_data(hass)[SERVERS]
    if not servers:
        raise HomeAssistantError("No Plex servers available")

    if plex_server_id:
        return servers[plex_server_id]

    plex_servers = servers.values()
    if plex_server_name:
        plex_server = next(
            (x for x in plex_servers if x.friendly_name == plex_server_name), None
        )
        if plex_server is not None:
            return plex_server
        friendly_names = [x.friendly_name for x in plex_servers]
        raise HomeAssistantError(
            f"Requested Plex server '{plex_server_name}' not found in {friendly_names}"
        )

    if len(plex_servers) == 1:
        return next(iter(plex_servers))

    friendly_names = [x.friendly_name for x in plex_servers]
    raise HomeAssistantError(
        "Multiple Plex servers configured, choose with 'plex_server' key:"
        f" {friendly_names}"
    )