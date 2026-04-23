def async_client_is_connected_fn(hub: UnifiHub, obj_id: str) -> bool:
    """Check if device object is disabled."""
    client = hub.api.clients[obj_id]

    if hub.entity_loader.wireless_clients.is_wireless(client) and client.is_wired:
        if not hub.config.option_ignore_wired_bug:
            return False  # Wired bug in action

    if (
        not client.is_wired
        and client.essid
        and hub.config.option_ssid_filter
        and client.essid not in hub.config.option_ssid_filter
    ):
        return False

    if (
        dt_util.utcnow() - dt_util.utc_from_timestamp(client.last_seen or 0)
        > hub.config.option_detection_time
    ):
        return False

    return True