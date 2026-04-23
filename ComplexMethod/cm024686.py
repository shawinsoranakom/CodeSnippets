async def test_switch_read_outlet_state(
    hass: HomeAssistant, get_next_aid: Callable[[], int]
) -> None:
    """Test that we can read the state of a HomeKit outlet accessory."""
    helper = await setup_test_component(hass, get_next_aid(), create_switch_service)

    # Initial state is that the switch is off and the outlet isn't in use
    switch_1 = await helper.poll_and_get_state()
    assert switch_1.state == "off"
    assert switch_1.attributes["outlet_in_use"] is False

    # Simulate that someone switched on the device in the real world not via HA
    switch_1 = await helper.async_update(
        ServicesTypes.OUTLET,
        {CharacteristicsTypes.ON: True},
    )
    assert switch_1.state == "on"
    assert switch_1.attributes["outlet_in_use"] is False

    # Simulate that device switched off in the real world not via HA
    switch_1 = await helper.async_update(
        ServicesTypes.OUTLET,
        {CharacteristicsTypes.ON: False},
    )
    assert switch_1.state == "off"

    # Simulate that someone plugged something into the device
    switch_1 = await helper.async_update(
        ServicesTypes.OUTLET,
        {CharacteristicsTypes.OUTLET_IN_USE: True},
    )
    assert switch_1.state == "off"
    assert switch_1.attributes["outlet_in_use"] is True