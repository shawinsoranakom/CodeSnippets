async def test_sending_mqtt_commands_support_open_and_optimistic(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test open function of the lock without state topic."""
    mqtt_mock = await mqtt_mock_entry()

    state = hass.states.get("lock.test")
    assert state.state == LockState.UNLOCKED
    assert state.attributes.get(ATTR_ASSUMED_STATE)
    assert state.attributes.get(ATTR_SUPPORTED_FEATURES) == LockEntityFeature.OPEN

    await hass.services.async_call(
        lock.DOMAIN, SERVICE_LOCK, {ATTR_ENTITY_ID: "lock.test"}, blocking=True
    )

    mqtt_mock.async_publish.assert_called_once_with("command-topic", "LOCK", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("lock.test")
    assert state.state == LockState.LOCKED
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await hass.services.async_call(
        lock.DOMAIN, SERVICE_UNLOCK, {ATTR_ENTITY_ID: "lock.test"}, blocking=True
    )

    mqtt_mock.async_publish.assert_called_once_with("command-topic", "UNLOCK", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("lock.test")
    assert state.state == LockState.UNLOCKED
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await hass.services.async_call(
        lock.DOMAIN, SERVICE_OPEN, {ATTR_ENTITY_ID: "lock.test"}, blocking=True
    )

    mqtt_mock.async_publish.assert_called_once_with("command-topic", "OPEN", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("lock.test")
    assert state.state == LockState.OPEN
    assert state.attributes.get(ATTR_ASSUMED_STATE)