async def test_one_lock_operation(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test creation of a lock with doorsense and bridge."""
    lock_one = await _mock_doorsense_enabled_yale_lock_detail(hass)
    await _create_yale_with_devices(hass, [lock_one])

    lock_state = hass.states.get("lock.online_with_doorsense_name")

    assert lock_state.state == LockState.LOCKED

    assert lock_state.attributes["battery_level"] == 92
    assert lock_state.attributes["friendly_name"] == "online_with_doorsense Name"

    data = {ATTR_ENTITY_ID: "lock.online_with_doorsense_name"}
    await hass.services.async_call(LOCK_DOMAIN, SERVICE_UNLOCK, data, blocking=True)

    lock_state = hass.states.get("lock.online_with_doorsense_name")
    assert lock_state.state == LockState.UNLOCKED

    assert lock_state.attributes["battery_level"] == 92
    assert lock_state.attributes["friendly_name"] == "online_with_doorsense Name"

    await hass.services.async_call(LOCK_DOMAIN, SERVICE_LOCK, data, blocking=True)

    lock_state = hass.states.get("lock.online_with_doorsense_name")
    assert lock_state.state == LockState.LOCKED

    # No activity means it will be unavailable until the activity feed has data
    assert entity_registry.async_get("sensor.online_with_doorsense_name_operator")
    operator_state = hass.states.get("sensor.online_with_doorsense_name_operator")
    assert operator_state.state == STATE_UNKNOWN