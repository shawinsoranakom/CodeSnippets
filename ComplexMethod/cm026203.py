def async_client_allowed_fn(hub: UnifiHub, obj_id: str) -> bool:
    """Check if client is allowed."""
    if obj_id in hub.config.option_supported_clients:
        return True

    if not hub.config.option_track_clients:
        return False

    client = hub.api.clients[obj_id]
    if client.mac not in hub.entity_loader.wireless_clients:
        if not hub.config.option_track_wired_clients:
            return False

    elif (
        client.essid
        and hub.config.option_ssid_filter
        and client.essid not in hub.config.option_ssid_filter
    ):
        return False

    return True