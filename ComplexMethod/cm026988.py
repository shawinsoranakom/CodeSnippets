async def websocket_network_status(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Get the status of the Z-Wave JS network."""
    if ENTRY_ID in msg:
        _, client, driver = await _async_get_entry(hass, connection, msg, msg[ENTRY_ID])
        if not client or not driver:
            return
    elif DEVICE_ID in msg:
        node = await _async_get_node(hass, connection, msg, msg[DEVICE_ID])
        if not node:
            return
        client = node.client
        assert client.driver
        driver = client.driver
    else:
        connection.send_error(
            msg[ID], ERR_INVALID_FORMAT, "Must specify either device_id or entry_id"
        )
        return
    controller = driver.controller
    controller.update(await controller.async_get_state())
    client_version_info = client.version
    assert client_version_info  # When client is connected version info is set.
    data = {
        "client": {
            "ws_server_url": client.ws_server_url,
            "state": "connected" if client.connected else "disconnected",
            "driver_version": client_version_info.driver_version,
            "server_version": client_version_info.server_version,
            "server_logging_enabled": client.server_logging_enabled,
        },
        "controller": {
            "home_id": controller.home_id,
            "sdk_version": controller.sdk_version,
            "type": controller.controller_type,
            "own_node_id": controller.own_node_id,
            "is_primary": controller.is_primary,
            "is_using_home_id_from_other_network": (
                controller.is_using_home_id_from_other_network
            ),
            "is_sis_present": controller.is_SIS_present,
            "was_real_primary": controller.was_real_primary,
            "is_suc": controller.is_suc,
            "node_type": controller.node_type,
            "firmware_version": controller.firmware_version,
            "manufacturer_id": controller.manufacturer_id,
            "product_id": controller.product_id,
            "product_type": controller.product_type,
            "supported_function_types": controller.supported_function_types,
            "suc_node_id": controller.suc_node_id,
            "supports_timers": controller.supports_timers,
            "supports_long_range": controller.supports_long_range,
            "is_rebuilding_routes": controller.is_rebuilding_routes,
            "inclusion_state": controller.inclusion_state,
            "rf_region": controller.rf_region,
            "status": controller.status,
            "nodes": [node_status(node) for node in driver.controller.nodes.values()],
        },
    }
    connection.send_result(
        msg[ID],
        data,
    )