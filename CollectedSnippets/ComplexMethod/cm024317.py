async def test_sending_mqtt_commands_pessimistic(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test function of the lock with state topics."""
    mqtt_mock = await mqtt_mock_entry()

    state = hass.states.get("lock.test")
    assert state.state is STATE_UNKNOWN
    assert state.attributes.get(ATTR_SUPPORTED_FEATURES) == LockEntityFeature.OPEN

    # send lock command to lock
    await hass.services.async_call(
        lock.DOMAIN, SERVICE_LOCK, {ATTR_ENTITY_ID: "lock.test"}, blocking=True
    )

    mqtt_mock.async_publish.assert_called_once_with("command-topic", "LOCK", 0, False)
    mqtt_mock.async_publish.reset_mock()

    # receive state from lock
    async_fire_mqtt_message(hass, "state-topic", "LOCKED")
    await hass.async_block_till_done()

    state = hass.states.get("lock.test")
    assert state.state == LockState.LOCKED

    await hass.services.async_call(
        lock.DOMAIN, SERVICE_UNLOCK, {ATTR_ENTITY_ID: "lock.test"}, blocking=True
    )

    mqtt_mock.async_publish.assert_called_once_with("command-topic", "UNLOCK", 0, False)
    mqtt_mock.async_publish.reset_mock()

    # receive state from lock
    async_fire_mqtt_message(hass, "state-topic", "UNLOCKED")
    await hass.async_block_till_done()

    state = hass.states.get("lock.test")
    assert state.state == LockState.UNLOCKED

    await hass.services.async_call(
        lock.DOMAIN, SERVICE_OPEN, {ATTR_ENTITY_ID: "lock.test"}, blocking=True
    )

    mqtt_mock.async_publish.assert_called_once_with("command-topic", "OPEN", 0, False)
    mqtt_mock.async_publish.reset_mock()

    # receive state from lock
    async_fire_mqtt_message(hass, "state-topic", "UNLOCKED")
    await hass.async_block_till_done()

    state = hass.states.get("lock.test")
    assert state.state == LockState.UNLOCKED

    # send lock command to lock
    await hass.services.async_call(
        lock.DOMAIN, SERVICE_LOCK, {ATTR_ENTITY_ID: "lock.test"}, blocking=True
    )

    # Go to locking state
    mqtt_mock.async_publish.assert_called_once_with("command-topic", "LOCK", 0, False)
    mqtt_mock.async_publish.reset_mock()

    # receive locking state from lock
    async_fire_mqtt_message(hass, "state-topic", "LOCKING")
    await hass.async_block_till_done()

    state = hass.states.get("lock.test")
    assert state.state == LockState.LOCKING

    # receive jammed state from lock
    async_fire_mqtt_message(hass, "state-topic", "JAMMED")
    await hass.async_block_till_done()

    state = hass.states.get("lock.test")
    assert state.state == LockState.JAMMED

    # receive solved state from lock
    async_fire_mqtt_message(hass, "state-topic", "LOCKED")
    await hass.async_block_till_done()

    state = hass.states.get("lock.test")
    assert state.state == LockState.LOCKED