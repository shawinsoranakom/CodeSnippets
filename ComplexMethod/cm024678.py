async def test_switch_read_alarm_state(
    hass: HomeAssistant, get_next_aid: Callable[[], int]
) -> None:
    """Test that we can read the state of a HomeKit alarm accessory."""
    helper = await setup_test_component(
        hass, get_next_aid(), create_security_system_service
    )

    await helper.async_update(
        ServicesTypes.SECURITY_SYSTEM,
        {CharacteristicsTypes.SECURITY_SYSTEM_STATE_CURRENT: 0},
    )
    state = await helper.poll_and_get_state()
    assert state.state == "armed_home"
    assert state.attributes["battery_level"] == 50
    assert state.attributes[ATTR_CODE_ARM_REQUIRED] is False

    await helper.async_update(
        ServicesTypes.SECURITY_SYSTEM,
        {CharacteristicsTypes.SECURITY_SYSTEM_STATE_CURRENT: 1},
    )
    state = await helper.poll_and_get_state()
    assert state.state == "armed_away"

    await helper.async_update(
        ServicesTypes.SECURITY_SYSTEM,
        {CharacteristicsTypes.SECURITY_SYSTEM_STATE_CURRENT: 2},
    )
    state = await helper.poll_and_get_state()
    assert state.state == "armed_night"

    await helper.async_update(
        ServicesTypes.SECURITY_SYSTEM,
        {CharacteristicsTypes.SECURITY_SYSTEM_STATE_CURRENT: 3},
    )
    state = await helper.poll_and_get_state()
    assert state.state == "disarmed"

    await helper.async_update(
        ServicesTypes.SECURITY_SYSTEM,
        {CharacteristicsTypes.SECURITY_SYSTEM_STATE_CURRENT: 4},
    )
    state = await helper.poll_and_get_state()
    assert state.state == "triggered"