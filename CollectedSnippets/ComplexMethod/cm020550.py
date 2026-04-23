async def test_switch(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test setup and state change of a switch device."""
    entry = configure_integration(hass)
    test_gateway = HomeControlMockSwitch()
    with patch(
        "homeassistant.components.devolo_home_control.HomeControl",
        side_effect=[test_gateway, HomeControlMock()],
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get(f"{SWITCH_DOMAIN}.test")
    assert state == snapshot
    assert entity_registry.async_get(f"{SWITCH_DOMAIN}.test") == snapshot

    # Emulate websocket message: switched on
    test_gateway.devices["Test"].binary_switch_property[
        "devolo.BinarySwitch:Test"
    ].state = True
    test_gateway.publisher.dispatch("Test", ("devolo.BinarySwitch:Test", True))
    await hass.async_block_till_done()
    assert hass.states.get(f"{SWITCH_DOMAIN}.test").state == STATE_ON

    with patch(
        "devolo_home_control_api.properties.binary_switch_property.BinarySwitchProperty.set"
    ) as set_value:
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: f"{SWITCH_DOMAIN}.test"},
            blocking=True,
        )  # In reality, this leads to a websocket message like already tested above
        set_value.assert_called_once_with(state=True)

        set_value.reset_mock()
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: f"{SWITCH_DOMAIN}.test"},
            blocking=True,
        )  # In reality, this leads to a websocket message like already tested above
        set_value.assert_called_once_with(state=False)

    # Emulate websocket message: device went offline
    test_gateway.devices["Test"].status = 1
    test_gateway.publisher.dispatch("Test", ("Status", False, "status"))
    await hass.async_block_till_done()
    assert hass.states.get(f"{SWITCH_DOMAIN}.test").state == STATE_UNAVAILABLE
    assert "Device Test is unavailable" in caplog.text

    # Emulate websocket message: device went back online
    test_gateway.devices["Test"].status = 0
    test_gateway.publisher.dispatch("Test", ("Status", False, "status"))
    await hass.async_block_till_done()
    assert hass.states.get(f"{SWITCH_DOMAIN}.test").state == STATE_ON
    assert "Device Test is back online" in caplog.text