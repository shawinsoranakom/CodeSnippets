async def test_status_subscription_done(
    hass: HomeAssistant,
    mqtt_client_mock: MqttMockPahoClient,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    recorded_calls: list[ReceiveMessage],
    record_calls: MessageCallbackType,
) -> None:
    """Test the on subscription status."""
    await mqtt_mock_entry()

    on_status = asyncio.Event()
    on_status_calls: list[bool] = []

    def _on_subscribe_status() -> None:
        on_status.set()
        on_status_calls.append(True)

    subscribe_callback = await mqtt.async_subscribe(
        hass, "test-topic", record_calls, qos=0
    )
    handler = mqtt.async_on_subscribe_done(
        hass, "test-topic", 0, on_subscribe_status=_on_subscribe_status
    )
    await on_status.wait()
    assert ("test-topic", 0) in help_all_subscribe_calls(mqtt_client_mock)

    await mqtt.async_publish(hass, "test-topic", "beer ready", 0)
    handler()
    assert len(recorded_calls) == 1
    assert recorded_calls[0].topic == "test-topic"
    assert recorded_calls[0].payload == "beer ready"
    assert recorded_calls[0].qos == 0

    # Test as we have an existing subscription, test we get a callback
    recorded_calls.clear()
    on_status.clear()
    handler = mqtt.async_on_subscribe_done(
        hass, "test-topic", 0, on_subscribe_status=_on_subscribe_status
    )
    assert len(on_status_calls) == 1
    await on_status.wait()
    assert len(on_status_calls) == 2

    # cleanup
    handler()
    subscribe_callback()