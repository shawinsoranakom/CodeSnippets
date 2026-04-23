def _get_node_statistics_dict(
    hass: HomeAssistant, statistics: NodeStatistics
) -> dict[str, Any]:
    """Get dictionary of node statistics."""
    dev_reg = dr.async_get(hass)

    def _convert_node_to_device_id(node: Node) -> str:
        """Convert a node to a device id."""
        driver = node.client.driver
        assert driver
        device = dev_reg.async_get_device(identifiers={get_device_id(driver, node)})
        assert device
        return device.id

    data: dict = {
        "commands_tx": statistics.commands_tx,
        "commands_rx": statistics.commands_rx,
        "commands_dropped_tx": statistics.commands_dropped_tx,
        "commands_dropped_rx": statistics.commands_dropped_rx,
        "timeout_response": statistics.timeout_response,
        "rtt": statistics.rtt,
        "rssi": statistics.rssi,
        "lwr": statistics.lwr.as_dict() if statistics.lwr else None,
        "nlwr": statistics.nlwr.as_dict() if statistics.nlwr else None,
    }
    for key in ("lwr", "nlwr"):
        if not data[key]:
            continue
        for key_2 in ("repeaters", "route_failed_between"):
            if not data[key][key_2]:
                continue
            data[key][key_2] = [
                _convert_node_to_device_id(node) for node in data[key][key_2]
            ]

    return data