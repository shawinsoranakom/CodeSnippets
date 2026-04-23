def async_device_clients_value_fn(hub: UnifiHub, device: Device) -> int:
    """Calculate the amount of clients connected to a device."""

    return len(
        [
            client.mac
            for client in hub.api.clients.values()
            if (
                (
                    client.access_point_mac != ""
                    and client.access_point_mac == device.mac
                )
                or (client.access_point_mac == "" and client.switch_mac == device.mac)
            )
            and dt_util.utcnow() - dt_util.utc_from_timestamp(client.last_seen or 0)
            < hub.config.option_detection_time
        ]
    )