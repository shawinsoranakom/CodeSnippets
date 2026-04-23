async def test_valve_read_state(
    hass: HomeAssistant, get_next_aid: Callable[[], int]
) -> None:
    """Test that we can read the state of a valve accessory."""
    helper = await setup_test_component(hass, get_next_aid(), create_valve_service)

    # Initial state is that the switch is off and the outlet isn't in use
    switch_1 = await helper.poll_and_get_state()
    assert switch_1.state == "off"
    assert switch_1.attributes["in_use"] is True
    assert switch_1.attributes["is_configured"] is True
    assert switch_1.attributes["remaining_duration"] == 99

    # Simulate that someone switched on the device in the real world not via HA
    switch_1 = await helper.async_update(
        ServicesTypes.VALVE,
        {CharacteristicsTypes.ACTIVE: True},
    )
    assert switch_1.state == "on"

    # Simulate that someone configured the device in the real world not via HA
    switch_1 = await helper.async_update(
        ServicesTypes.VALVE,
        {CharacteristicsTypes.IS_CONFIGURED: IsConfiguredValues.NOT_CONFIGURED},
    )
    assert switch_1.attributes["is_configured"] is False

    # Simulate that someone using the device in the real world not via HA
    switch_1 = await helper.async_update(
        ServicesTypes.VALVE,
        {CharacteristicsTypes.IN_USE: InUseValues.NOT_IN_USE},
    )
    assert switch_1.attributes["in_use"] is False