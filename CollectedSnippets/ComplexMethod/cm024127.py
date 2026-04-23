async def test_subscribe_connection_status(
    hass: HomeAssistant,
    mock_debouncer: asyncio.Event,
    setup_with_birth_msg_client_mock: MqttMockPahoClient,
) -> None:
    """Test connextion status subscription."""

    mqtt_client_mock = setup_with_birth_msg_client_mock
    mqtt_connected_calls_callback: list[bool] = []
    mqtt_connected_calls_async: list[bool] = []

    @callback
    def async_mqtt_connected_callback(status: bool) -> None:
        """Update state on connection/disconnection to MQTT broker."""
        mqtt_connected_calls_callback.append(status)

    async def async_mqtt_connected_async(status: bool) -> None:
        """Update state on connection/disconnection to MQTT broker."""
        mqtt_connected_calls_async.append(status)

    # Check connection status
    assert mqtt.is_connected(hass) is True

    # Mock disconnect status
    mqtt_client_mock.on_disconnect(None, None, 0, MockMqttReasonCode())
    await hass.async_block_till_done()
    assert mqtt.is_connected(hass) is False

    unsub_callback = mqtt.async_subscribe_connection_status(
        hass, async_mqtt_connected_callback
    )
    unsub_async = mqtt.async_subscribe_connection_status(
        hass, async_mqtt_connected_async
    )
    await hass.async_block_till_done()

    # Mock connect status
    mock_debouncer.clear()
    mqtt_client_mock.on_connect(None, None, 0, MockMqttReasonCode())
    await mock_debouncer.wait()
    assert mqtt.is_connected(hass) is True

    # Mock disconnect status
    mqtt_client_mock.on_disconnect(None, None, 0, MockMqttReasonCode())
    await hass.async_block_till_done()
    assert mqtt.is_connected(hass) is False

    # Unsubscribe
    unsub_callback()
    unsub_async()

    # Mock connect status
    mock_debouncer.clear()
    mqtt_client_mock.on_connect(None, None, 0, MockMqttReasonCode())
    await mock_debouncer.wait()
    assert mqtt.is_connected(hass) is True

    # Check calls
    assert len(mqtt_connected_calls_callback) == 2
    assert mqtt_connected_calls_callback[0] is True
    assert mqtt_connected_calls_callback[1] is False

    assert len(mqtt_connected_calls_async) == 2
    assert mqtt_connected_calls_async[0] is True
    assert mqtt_connected_calls_async[1] is False