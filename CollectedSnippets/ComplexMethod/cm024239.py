async def test_mqtt_subscribes_and_unsubscribes_in_chunks(
    hass: HomeAssistant,
    mock_debouncer: asyncio.Event,
    setup_with_birth_msg_client_mock: MqttMockPahoClient,
    record_calls: MessageCallbackType,
) -> None:
    """Test chunked client subscriptions."""
    mqtt_client_mock = setup_with_birth_msg_client_mock

    mqtt_client_mock.subscribe.reset_mock()
    unsub_tasks: list[CALLBACK_TYPE] = []
    mock_debouncer.clear()
    unsub_tasks.append(await mqtt.async_subscribe(hass, "topic/test1", record_calls))
    unsub_tasks.append(await mqtt.async_subscribe(hass, "home/sensor1", record_calls))
    unsub_tasks.append(await mqtt.async_subscribe(hass, "topic/test2", record_calls))
    unsub_tasks.append(await mqtt.async_subscribe(hass, "home/sensor2", record_calls))
    # Make sure the debouncer finishes
    await mock_debouncer.wait()

    assert mqtt_client_mock.subscribe.call_count == 2
    # Assert we have a 2 subscription calls with both 2 subscriptions
    assert len(mqtt_client_mock.subscribe.mock_calls[0][1][0]) == 2
    assert len(mqtt_client_mock.subscribe.mock_calls[1][1][0]) == 2

    # Unsubscribe all topics
    mock_debouncer.clear()
    for task in unsub_tasks:
        task()
    # Make sure the debouncer finishes
    await mock_debouncer.wait()

    assert mqtt_client_mock.unsubscribe.call_count == 2
    # Assert we have a 2 unsubscribe calls with both 2 topic
    assert len(mqtt_client_mock.unsubscribe.mock_calls[0][1][0]) == 2
    assert len(mqtt_client_mock.unsubscribe.mock_calls[1][1][0]) == 2