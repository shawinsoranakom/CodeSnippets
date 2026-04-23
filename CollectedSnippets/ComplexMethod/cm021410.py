async def test_switch(
    hass: HomeAssistant, mock_bridge, mock_api, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test the switch."""
    await init_integration(hass)
    assert mock_bridge

    device = DUMMY_WATER_HEATER_DEVICE
    entity_id = f"{SWITCH_DOMAIN}.{slugify(device.name)}"

    # Test initial state - on
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON

    # Test state change on --> off
    monkeypatch.setattr(device, "device_state", DeviceState.OFF)
    mock_bridge.mock_callbacks([DUMMY_WATER_HEATER_DEVICE])
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF

    # Test turning on
    with patch(
        "homeassistant.components.switcher_kis.entity.SwitcherApi.control_device",
    ) as mock_control_device:
        await hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )

        assert mock_api.call_count == 2
        mock_control_device.assert_called_once_with(Command.ON)
        state = hass.states.get(entity_id)
        assert state.state == STATE_ON

    # Test turning off
    with patch(
        "homeassistant.components.switcher_kis.entity.SwitcherApi.control_device"
    ) as mock_control_device:
        await hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )

        assert mock_api.call_count == 4
        mock_control_device.assert_called_once_with(Command.OFF)
        state = hass.states.get(entity_id)
        assert state.state == STATE_OFF