async def test_modify_topics(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test modification of topics."""
    await mqtt_mock_entry()
    calls1 = []

    @callback
    def record_calls1(*args):
        """Record calls."""
        calls1.append(args)

    calls2 = []

    @callback
    def record_calls2(*args):
        """Record calls."""
        calls2.append(args)

    sub_state = None
    sub_state = async_prepare_subscribe_topics(
        hass,
        sub_state,
        {
            "test_topic1": {"topic": "test-topic1", "msg_callback": record_calls1},
            "test_topic2": {"topic": "test-topic2", "msg_callback": record_calls2},
        },
    )
    await async_subscribe_topics(hass, sub_state)

    async_fire_mqtt_message(hass, "test-topic1", "test-payload")
    assert len(calls1) == 1
    assert len(calls2) == 0

    async_fire_mqtt_message(hass, "test-topic2", "test-payload")
    assert len(calls1) == 1
    assert len(calls2) == 1

    sub_state = async_prepare_subscribe_topics(
        hass,
        sub_state,
        {"test_topic1": {"topic": "test-topic1_1", "msg_callback": record_calls1}},
    )
    await async_subscribe_topics(hass, sub_state)

    async_fire_mqtt_message(hass, "test-topic1", "test-payload")
    async_fire_mqtt_message(hass, "test-topic2", "test-payload")
    assert len(calls1) == 1
    assert len(calls2) == 1

    async_fire_mqtt_message(hass, "test-topic1_1", "test-payload")
    assert len(calls1) == 2
    assert calls1[1][0].topic == "test-topic1_1"
    assert calls1[1][0].payload == "test-payload"
    assert len(calls2) == 1

    async_unsubscribe_topics(hass, sub_state)

    async_fire_mqtt_message(hass, "test-topic1_1", "test-payload")
    async_fire_mqtt_message(hass, "test-topic2", "test-payload")

    assert len(calls1) == 2
    assert len(calls2) == 1