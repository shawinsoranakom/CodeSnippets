async def test_failing_hass_operations(
    hass: HomeAssistant, numato_fixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test failing operations called from within Home Assistant.

    Switches remain in their initial 'off' state when the device can't
    be written to.
    """
    assert await async_setup_component(hass, "numato", NUMATO_CFG)

    await hass.async_block_till_done()  # wait until services are registered
    monkeypatch.setattr(numato_fixture.devices[0], "write", mockup_raise)
    await hass.services.async_call(
        switch.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.numato_switch_mock_port5"},
        blocking=True,
    )
    assert hass.states.get("switch.numato_switch_mock_port5").state == "off"
    assert not numato_fixture.devices[0].values[5]
    await hass.services.async_call(
        switch.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.numato_switch_mock_port6"},
        blocking=True,
    )
    assert hass.states.get("switch.numato_switch_mock_port6").state == "off"
    assert not numato_fixture.devices[0].values[6]
    await hass.services.async_call(
        switch.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.numato_switch_mock_port5"},
        blocking=True,
    )
    assert hass.states.get("switch.numato_switch_mock_port5").state == "off"
    assert not numato_fixture.devices[0].values[5]
    await hass.services.async_call(
        switch.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.numato_switch_mock_port6"},
        blocking=True,
    )
    assert hass.states.get("switch.numato_switch_mock_port6").state == "off"
    assert not numato_fixture.devices[0].values[6]