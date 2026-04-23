async def test_one_lock_operation(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test creation of a lock with doorsense and bridge."""
    lock_one = await _mock_doorsense_enabled_august_lock_detail(hass)
    await _create_august_with_devices(hass, [lock_one])
    states = hass.states

    lock_state = states.get("lock.online_with_doorsense_name")

    assert lock_state.state == LockState.LOCKED

    assert lock_state.attributes["battery_level"] == 92
    assert lock_state.attributes["friendly_name"] == "online_with_doorsense Name"

    data = {ATTR_ENTITY_ID: "lock.online_with_doorsense_name"}
    await hass.services.async_call(LOCK_DOMAIN, SERVICE_UNLOCK, data, blocking=True)

    lock_state = states.get("lock.online_with_doorsense_name")
    assert lock_state.state == LockState.UNLOCKED

    assert lock_state.attributes["battery_level"] == 92
    assert lock_state.attributes["friendly_name"] == "online_with_doorsense Name"

    await hass.services.async_call(LOCK_DOMAIN, SERVICE_LOCK, data, blocking=True)

    assert states.get("lock.online_with_doorsense_name").state == LockState.LOCKED

    # No activity means it will be unavailable until the activity feed has data
    lock_operator_sensor = entity_registry.async_get(
        "sensor.online_with_doorsense_name_operator"
    )
    assert lock_operator_sensor
    assert (
        states.get("sensor.online_with_doorsense_name_operator").state == STATE_UNKNOWN
    )