async def test_on_off_switch_state(
    hass: HomeAssistant, dummy_device_from_host_switch
) -> None:
    """Test the change of state of the switch."""
    await setup_integration(hass)

    # On - watering
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.wl000000000099_1_watering"},
        blocking=True,
    )

    await hass.async_block_till_done()
    state = hass.states.get("switch.wl000000000099_1_watering")
    assert state
    assert state.state == STATE_ON

    # Off - watering
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.wl000000000099_1_watering"},
        blocking=True,
    )

    await hass.async_block_till_done()
    state = hass.states.get("switch.wl000000000099_1_watering")
    assert state
    assert state.state == STATE_OFF

    # On - pause
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.wl000000000099_2_pause"},
        blocking=True,
    )

    await hass.async_block_till_done()
    state = hass.states.get("switch.wl000000000099_2_pause")
    assert state
    assert state.state == STATE_ON

    # Off - pause
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.wl000000000099_2_pause"},
        blocking=True,
    )

    await hass.async_block_till_done()
    state = hass.states.get("switch.wl000000000099_2_pause")
    assert state
    assert state.state == STATE_OFF