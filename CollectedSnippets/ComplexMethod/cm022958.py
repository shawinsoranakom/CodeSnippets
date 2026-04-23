async def test_on_off_fan_state(
    hass: HomeAssistant, dummy_device_from_host_light_fan
) -> None:
    """Test the change of state of the fan switches."""
    await setup_integration(hass)

    # Turn on
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "fan.wl000000000099_2"},
        blocking=True,
    )

    await hass.async_block_till_done()
    state = hass.states.get("fan.wl000000000099_2")
    assert state
    assert state.state == STATE_ON

    # Turn on with speed
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_PERCENTAGE: 30, ATTR_ENTITY_ID: "fan.wl000000000099_2"},
        blocking=True,
    )

    await hass.async_block_till_done()
    state = hass.states.get("fan.wl000000000099_2")
    assert state
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_PERCENTAGE) == 33

    # Turn off
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "fan.wl000000000099_2"},
        blocking=True,
    )

    await hass.async_block_till_done()
    state = hass.states.get("fan.wl000000000099_2")
    assert state
    assert state.state == STATE_OFF