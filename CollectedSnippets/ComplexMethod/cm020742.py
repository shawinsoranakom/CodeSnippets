async def test_unlock_operator_manual(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test operation of a lock manually."""
    lock_one = await _mock_doorsense_enabled_august_lock_detail(hass)

    activities = await _mock_activities_from_fixture(
        hass, "get_activity.unlock_from_manual.json"
    )
    await _create_august_with_devices(hass, [lock_one], activities=activities)

    lock_operator_sensor = entity_registry.async_get(
        "sensor.online_with_doorsense_name_operator"
    )
    assert lock_operator_sensor

    state = hass.states.get("sensor.online_with_doorsense_name_operator")
    assert state.state == "Your favorite elven princess"
    assert state.attributes["manual"] is True
    assert state.attributes["tag"] is False
    assert state.attributes["remote"] is False
    assert state.attributes["keypad"] is False
    assert state.attributes["autorelock"] is False
    assert state.attributes["method"] == "manual"