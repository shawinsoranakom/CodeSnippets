async def test_init(hass: HomeAssistant, mock_entry) -> None:
    """Test platform setup."""

    mock_entry.add_to_hass(hass)

    mock_light_1 = MagicMock(spec=pyzerproc.Light)
    mock_light_1.address = "AA:BB:CC:DD:EE:FF"
    mock_light_1.name = "LEDBlue-CCDDEEFF"
    mock_light_1.is_connected.return_value = True

    mock_light_2 = MagicMock(spec=pyzerproc.Light)
    mock_light_2.address = "11:22:33:44:55:66"
    mock_light_2.name = "LEDBlue-33445566"
    mock_light_2.is_connected.return_value = True

    mock_state_1 = pyzerproc.LightState(False, (0, 0, 0))
    mock_state_2 = pyzerproc.LightState(True, (0, 80, 255))

    mock_light_1.get_state.return_value = mock_state_1
    mock_light_2.get_state.return_value = mock_state_2

    with patch(
        "homeassistant.components.zerproc.light.pyzerproc.discover",
        return_value=[mock_light_1, mock_light_2],
    ):
        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("light.ledblue_ccddeeff")
    assert state.state == STATE_OFF
    assert state.attributes == {
        ATTR_FRIENDLY_NAME: "LEDBlue-CCDDEEFF",
        ATTR_SUPPORTED_COLOR_MODES: [ColorMode.HS],
        ATTR_SUPPORTED_FEATURES: 0,
        ATTR_COLOR_MODE: None,
        ATTR_BRIGHTNESS: None,
        ATTR_HS_COLOR: None,
        ATTR_RGB_COLOR: None,
        ATTR_XY_COLOR: None,
    }

    state = hass.states.get("light.ledblue_33445566")
    assert state.state == STATE_ON
    assert state.attributes == {
        ATTR_FRIENDLY_NAME: "LEDBlue-33445566",
        ATTR_SUPPORTED_COLOR_MODES: [ColorMode.HS],
        ATTR_SUPPORTED_FEATURES: 0,
        ATTR_COLOR_MODE: ColorMode.HS,
        ATTR_BRIGHTNESS: 255,
        ATTR_HS_COLOR: (221.176, 100.0),
        ATTR_RGB_COLOR: (0, 80, 255),
        ATTR_XY_COLOR: (0.138, 0.08),
    }

    with patch.object(hass.loop, "stop"):
        await hass.async_stop()

    assert mock_light_1.disconnect.called
    assert mock_light_2.disconnect.called

    assert hass.data[DOMAIN]["addresses"] == {"AA:BB:CC:DD:EE:FF", "11:22:33:44:55:66"}