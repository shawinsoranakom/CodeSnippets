async def test_light_update(hass: HomeAssistant, mock_light) -> None:
    """Test ZerprocLight update."""
    utcnow = dt_util.utcnow()

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

    # Make sure no discovery calls are made while we emulate time passing
    with patch("homeassistant.components.zerproc.light.pyzerproc.discover"):
        # Test an exception during discovery
        with patch.object(
            mock_light, "get_state", side_effect=pyzerproc.ZerprocException("TEST")
        ):
            utcnow = utcnow + SCAN_INTERVAL
            async_fire_time_changed(hass, utcnow)
            await hass.async_block_till_done()

        state = hass.states.get("light.ledblue_ccddeeff")
        assert state.state == STATE_UNAVAILABLE
        assert state.attributes == {
            ATTR_FRIENDLY_NAME: "LEDBlue-CCDDEEFF",
            ATTR_SUPPORTED_COLOR_MODES: [ColorMode.HS],
            ATTR_SUPPORTED_FEATURES: 0,
        }

        with patch.object(
            mock_light,
            "get_state",
            return_value=pyzerproc.LightState(False, (200, 128, 100)),
        ):
            utcnow = utcnow + SCAN_INTERVAL
            async_fire_time_changed(hass, utcnow)
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

        with patch.object(
            mock_light,
            "get_state",
            return_value=pyzerproc.LightState(True, (175, 150, 220)),
        ):
            utcnow = utcnow + SCAN_INTERVAL
            async_fire_time_changed(hass, utcnow)
            await hass.async_block_till_done()

        state = hass.states.get("light.ledblue_ccddeeff")
        assert state.state == STATE_ON
        assert state.attributes == {
            ATTR_FRIENDLY_NAME: "LEDBlue-CCDDEEFF",
            ATTR_SUPPORTED_COLOR_MODES: [ColorMode.HS],
            ATTR_SUPPORTED_FEATURES: 0,
            ATTR_COLOR_MODE: ColorMode.HS,
            ATTR_BRIGHTNESS: 220,
            ATTR_HS_COLOR: (261.429, 31.818),
            ATTR_RGB_COLOR: (203, 174, 255),
            ATTR_XY_COLOR: (0.292, 0.234),
        }