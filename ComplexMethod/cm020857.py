async def test_regular_hass_operations(hass: HomeAssistant, numato_fixture) -> None:
    """Test regular operations from within Home Assistant."""
    assert await async_setup_component(hass, "numato", NUMATO_CFG)
    await hass.async_block_till_done()  # wait until services are registered
    await hass.services.async_call(
        switch.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.numato_switch_mock_port5"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get("switch.numato_switch_mock_port5").state == "on"
    assert numato_fixture.devices[0].values[5] == 1
    await hass.services.async_call(
        switch.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.numato_switch_mock_port6"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get("switch.numato_switch_mock_port6").state == "on"
    assert numato_fixture.devices[0].values[6] == 1
    await hass.services.async_call(
        switch.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.numato_switch_mock_port5"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get("switch.numato_switch_mock_port5").state == "off"
    assert numato_fixture.devices[0].values[5] == 0
    await hass.services.async_call(
        switch.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.numato_switch_mock_port6"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get("switch.numato_switch_mock_port6").state == "off"
    assert numato_fixture.devices[0].values[6] == 0