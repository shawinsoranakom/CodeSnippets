async def test_lock_operator_autorelock(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test operation of a lock with doorsense and bridge."""
    lock_one = await _mock_doorsense_enabled_august_lock_detail(hass)

    activities = await _mock_activities_from_fixture(
        hass, "get_activity.lock_from_autorelock.json"
    )
    await _create_august_with_devices(hass, [lock_one], activities=activities)

    lock_operator_sensor = entity_registry.async_get(
        "sensor.online_with_doorsense_name_operator"
    )
    assert lock_operator_sensor

    state = hass.states.get("sensor.online_with_doorsense_name_operator")
    assert state.state == "Auto Relock"
    assert state.attributes["manual"] is False
    assert state.attributes["tag"] is False
    assert state.attributes["remote"] is False
    assert state.attributes["keypad"] is False
    assert state.attributes["autorelock"] is True
    assert state.attributes["method"] == "autorelock"