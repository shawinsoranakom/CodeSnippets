def _device_already_added(
    current_entries: list[ConfigEntry], user_input: dict[str, Any], protocol: str | None
) -> bool:
    """Determine if entry has already been added to HA."""
    user_host = user_input.get(CONF_HOST)
    user_port = user_input.get(CONF_PORT)
    user_path = user_input.get(CONF_DEVICE_PATH)
    user_baud = user_input.get(CONF_DEVICE_BAUD)

    for entry in current_entries:
        entry_host = entry.data.get(CONF_HOST)
        entry_port = entry.data.get(CONF_PORT)
        entry_path = entry.data.get(CONF_DEVICE_PATH)
        entry_baud = entry.data.get(CONF_DEVICE_BAUD)

        if (
            protocol == PROTOCOL_SOCKET
            and user_host == entry_host
            and user_port == entry_port
        ):
            return True

        if (
            protocol == PROTOCOL_SERIAL
            and user_baud == entry_baud
            and user_path == entry_path
        ):
            return True

    return False