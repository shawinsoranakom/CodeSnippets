async def test_replaying_payload_wildcard_topic(
    hass: HomeAssistant,
    mock_debouncer: asyncio.Event,
    setup_with_birth_msg_client_mock: MqttMockPahoClient,
) -> None:
    """Test replaying retained messages.

    When we have multiple subscriptions to the same wildcard topic,
    SUBSCRIBE must be sent to the broker again
    for it to resend any retained messages for new subscriptions.
    Retained messages should only be replayed for new subscriptions, except
    when the MQTT client is reconnection.
    """
    mqtt_client_mock = setup_with_birth_msg_client_mock
    calls_a: list[ReceiveMessage] = []
    calls_b: list[ReceiveMessage] = []

    @callback
    def _callback_a(msg: ReceiveMessage) -> None:
        calls_a.append(msg)

    @callback
    def _callback_b(msg: ReceiveMessage) -> None:
        calls_b.append(msg)

    mqtt_client_mock.reset_mock()
    mock_debouncer.clear()
    await mqtt.async_subscribe(hass, "test/#", _callback_a)
    await mock_debouncer.wait()
    # Simulate (retained) messages being played back on new subscriptions
    async_fire_mqtt_message(hass, "test/state1", "new_value_1", qos=0, retain=True)
    async_fire_mqtt_message(hass, "test/state2", "new_value_2", qos=0, retain=True)
    assert len(calls_a) == 2
    mqtt_client_mock.subscribe.assert_called()
    calls_a = []
    mqtt_client_mock.reset_mock()

    # resubscribe to the wild card topic again
    mock_debouncer.clear()
    await mqtt.async_subscribe(hass, "test/#", _callback_b)
    await mock_debouncer.wait()
    # Simulate (retained) messages being played back on new subscriptions
    async_fire_mqtt_message(hass, "test/state1", "initial_value_1", qos=0, retain=True)
    async_fire_mqtt_message(hass, "test/state2", "initial_value_2", qos=0, retain=True)
    # The retained messages playback should only be processed for the new subscriptions
    assert len(calls_a) == 0
    assert len(calls_b) == 2
    mqtt_client_mock.subscribe.assert_called()

    calls_a = []
    calls_b = []
    mqtt_client_mock.reset_mock()

    # Simulate new messages being received
    async_fire_mqtt_message(hass, "test/state1", "update_value_1", qos=0, retain=False)
    async_fire_mqtt_message(hass, "test/state2", "update_value_2", qos=0, retain=False)
    assert len(calls_a) == 2
    assert len(calls_b) == 2

    # Now simulate the broker was disconnected shortly
    calls_a = []
    calls_b = []
    mqtt_client_mock.reset_mock()
    mqtt_client_mock.on_disconnect(None, None, 0, MockMqttReasonCode())

    mock_debouncer.clear()
    mqtt_client_mock.on_connect(None, None, None, MockMqttReasonCode())
    await mock_debouncer.wait()

    mqtt_client_mock.subscribe.assert_called()
    # Simulate the (retained) messages are played back after reconnecting
    # for all subscriptions
    async_fire_mqtt_message(hass, "test/state1", "update_value_1", qos=0, retain=True)
    async_fire_mqtt_message(hass, "test/state2", "update_value_2", qos=0, retain=True)
    # Both subscriptions should replay
    assert len(calls_a) == 2
    assert len(calls_b) == 2