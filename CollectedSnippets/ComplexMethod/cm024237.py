async def test_replaying_payload_same_topic(
    hass: HomeAssistant,
    mock_debouncer: asyncio.Event,
    setup_with_birth_msg_client_mock: MqttMockPahoClient,
) -> None:
    """Test replaying retained messages.

    When subscribing to the same topic again, SUBSCRIBE must be sent to the broker again
    for it to resend any retained messages for new subscriptions.
    Retained messages must only be replayed for new subscriptions, except
    when the MQTT client is reconnecting.
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
    await mqtt.async_subscribe(hass, "test/state", _callback_a)
    await mock_debouncer.wait()
    async_fire_mqtt_message(
        hass, "test/state", "online", qos=0, retain=True
    )  # Simulate a (retained) message played back
    assert len(calls_a) == 1
    mqtt_client_mock.subscribe.assert_called()
    calls_a = []
    mqtt_client_mock.reset_mock()

    mock_debouncer.clear()
    await mqtt.async_subscribe(hass, "test/state", _callback_b)
    await mock_debouncer.wait()

    # Simulate edge case where non retained message was received
    # after subscription at HA but before the debouncer delay was passed.
    # The message without retain flag directly after a subscription should
    # be processed by both subscriptions.
    async_fire_mqtt_message(hass, "test/state", "online", qos=0, retain=False)

    # Simulate a (retained) message played back on new subscriptions
    async_fire_mqtt_message(hass, "test/state", "online", qos=0, retain=True)

    # The current subscription only received the message without retain flag
    assert len(calls_a) == 1
    assert help_assert_message(calls_a[0], "test/state", "online", qos=0, retain=False)
    # The retained message playback should only be processed by the new subscription.
    # The existing subscription already got the latest update, hence the existing
    # subscription should not receive the replayed (retained) message.
    # Messages without retain flag are received on both subscriptions.
    assert len(calls_b) == 2
    assert help_assert_message(calls_b[0], "test/state", "online", qos=0, retain=False)
    assert help_assert_message(calls_b[1], "test/state", "online", qos=0, retain=True)
    mqtt_client_mock.subscribe.assert_called()

    calls_a = []
    calls_b = []
    mqtt_client_mock.reset_mock()

    # Simulate new message played back on new subscriptions
    # After connecting the retain flag will not be set, even if the
    # payload published was retained, we cannot see that
    async_fire_mqtt_message(hass, "test/state", "online", qos=0, retain=False)
    assert len(calls_a) == 1
    assert help_assert_message(calls_a[0], "test/state", "online", qos=0, retain=False)
    assert len(calls_b) == 1
    assert help_assert_message(calls_b[0], "test/state", "online", qos=0, retain=False)

    # Now simulate the broker was disconnected shortly
    calls_a = []
    calls_b = []
    mqtt_client_mock.reset_mock()
    mqtt_client_mock.on_disconnect(None, None, 0, MockMqttReasonCode())

    mock_debouncer.clear()
    mqtt_client_mock.on_connect(None, None, None, MockMqttReasonCode())
    await mock_debouncer.wait()
    mqtt_client_mock.subscribe.assert_called()
    # Simulate a (retained) message played back after reconnecting
    async_fire_mqtt_message(hass, "test/state", "online", qos=0, retain=True)
    # Both subscriptions now should replay the retained message
    assert len(calls_a) == 1
    assert help_assert_message(calls_a[0], "test/state", "online", qos=0, retain=True)
    assert len(calls_b) == 1
    assert help_assert_message(calls_b[0], "test/state", "online", qos=0, retain=True)