async def test_remove_sensors(
    hass: HomeAssistant,
    mock_websocket_message: WebsocketMessageMock,
    client_payload: list[dict[str, Any]],
) -> None:
    """Verify removing of clients work as expected."""
    assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 7
    assert hass.states.get("sensor.wired_client_rx")
    assert hass.states.get("sensor.wired_client_tx")
    assert hass.states.get("sensor.wired_client_link_speed")
    assert hass.states.get("sensor.wired_client_uptime")
    assert hass.states.get("sensor.wireless_client_rx")
    assert hass.states.get("sensor.wireless_client_tx")
    assert hass.states.get("sensor.wireless_client_uptime")

    # Remove wired client
    mock_websocket_message(message=MessageKey.CLIENT_REMOVED, data=client_payload[0])
    await hass.async_block_till_done()

    assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 3
    assert hass.states.get("sensor.wired_client_rx") is None
    assert hass.states.get("sensor.wired_client_tx") is None
    assert hass.states.get("sensor.wired_client_link_speed") is None
    assert hass.states.get("sensor.wired_client_uptime") is None
    assert hass.states.get("sensor.wireless_client_rx")
    assert hass.states.get("sensor.wireless_client_tx")
    assert hass.states.get("sensor.wireless_client_uptime")