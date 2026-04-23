async def test_ceiling_light_turn_on(
    hass: HomeAssistant, mock_list_devices, mock_get_status, device_type
) -> None:
    """Test ceiling light turn on."""
    mock_list_devices.return_value = [
        Device(
            version="V1.0",
            deviceId="light-id-1",
            deviceName="light-1",
            deviceType=device_type,
            hubDeviceId="test-hub-id",
        ),
    ]
    mock_get_status.side_effect = [
        {"power": "off", "brightness": 1, "colorTemperature": 4567},
        {"power": "on", "brightness": 10, "colorTemperature": 5555},
        {"power": "on", "brightness": 10, "colorTemperature": 5555},
        {"power": "on", "brightness": 10, "colorTemperature": 5555},
        {"power": "on", "brightness": 10, "colorTemperature": 5555},
    ]
    entry = await configure_integration(hass)
    assert entry.state is ConfigEntryState.LOADED
    entity_id = "light.light_1"
    state = hass.states.get(entity_id)
    assert state.state is STATE_OFF

    # Test turn on with brightness
    with patch.object(SwitchBotAPI, "send_command") as mock_send_command:
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id, "brightness": 99},
            blocking=True,
        )
        mock_send_command.assert_called_with(
            "light-id-1",
            CeilingLightCommands.SET_BRIGHTNESS,
            "command",
            "38",
        )
    state = hass.states.get(entity_id)
    assert state.state is STATE_ON
    assert state.attributes[ATTR_COLOR_MODE] == ColorMode.COLOR_TEMP

    # Test turn on with color temp
    with patch.object(SwitchBotAPI, "send_command") as mock_send_command:
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id, "color_temp_kelvin": 3333},
            blocking=True,
        )
        mock_send_command.assert_called_with(
            "light-id-1",
            CeilingLightCommands.SET_COLOR_TEMPERATURE,
            "command",
            "3333",
        )
    state = hass.states.get(entity_id)
    assert state.state is STATE_ON

    # Test turn on without arguments
    with patch.object(SwitchBotAPI, "send_command") as mock_send_command:
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_send_command.assert_called_with(
            "light-id-1",
            CommonCommands.ON,
            "command",
            "default",
        )
    state = hass.states.get(entity_id)
    assert state.state is STATE_ON
    assert state.attributes[ATTR_COLOR_MODE] == ColorMode.COLOR_TEMP