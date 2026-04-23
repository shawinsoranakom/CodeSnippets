async def test_optimistic_state_change_with_position(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test changing state optimistically."""
    mqtt_mock = await mqtt_mock_entry()

    state = hass.states.get("cover.test")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get(ATTR_ASSUMED_STATE)
    assert state.attributes.get(ATTR_CURRENT_POSITION) is None

    await hass.services.async_call(
        cover.DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: "cover.test"}, blocking=True
    )

    mqtt_mock.async_publish.assert_called_once_with("command-topic", "OPEN", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("cover.test")
    assert state.state == CoverState.OPEN
    assert state.attributes.get(ATTR_CURRENT_POSITION) == 100

    await hass.services.async_call(
        cover.DOMAIN, SERVICE_CLOSE_COVER, {ATTR_ENTITY_ID: "cover.test"}, blocking=True
    )

    mqtt_mock.async_publish.assert_called_once_with("command-topic", "CLOSE", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("cover.test")
    assert state.state == CoverState.CLOSED
    assert state.attributes.get(ATTR_CURRENT_POSITION) == 0

    await hass.services.async_call(
        cover.DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: "cover.test"}, blocking=True
    )

    mqtt_mock.async_publish.assert_called_once_with("command-topic", "OPEN", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("cover.test")
    assert state.state == CoverState.OPEN
    assert state.attributes.get(ATTR_CURRENT_POSITION) == 100

    await hass.services.async_call(
        cover.DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: "cover.test"}, blocking=True
    )

    mqtt_mock.async_publish.assert_called_once_with("command-topic", "CLOSE", 0, False)
    state = hass.states.get("cover.test")
    assert state.state == CoverState.CLOSED
    assert state.attributes.get(ATTR_CURRENT_POSITION) == 0