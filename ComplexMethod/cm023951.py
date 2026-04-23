async def test_light_update(hass: HomeAssistant, mock_light: MagicMock) -> None:
    """Test KulerSkyLight update."""
    utcnow = dt_util.utcnow()

    state = hass.states.get("light.bedroom")
    assert state.state == STATE_OFF
    assert dict(state.attributes) == {
        ATTR_FRIENDLY_NAME: "Bedroom",
        ATTR_SUPPORTED_COLOR_MODES: [ColorMode.RGBW],
        ATTR_SUPPORTED_FEATURES: 0,
        ATTR_COLOR_MODE: None,
        ATTR_BRIGHTNESS: None,
        ATTR_HS_COLOR: None,
        ATTR_RGB_COLOR: None,
        ATTR_RGBW_COLOR: None,
        ATTR_XY_COLOR: None,
    }

    # Test an exception during discovery
    mock_light.get_color.side_effect = pykulersky.PykulerskyException("TEST")
    utcnow = utcnow + SCAN_INTERVAL
    async_fire_time_changed(hass, utcnow)
    await hass.async_block_till_done()

    state = hass.states.get("light.bedroom")
    assert state.state == STATE_UNAVAILABLE
    assert dict(state.attributes) == {
        ATTR_FRIENDLY_NAME: "Bedroom",
        ATTR_SUPPORTED_COLOR_MODES: [ColorMode.RGBW],
        ATTR_SUPPORTED_FEATURES: 0,
    }

    mock_light.get_color.side_effect = None
    mock_light.get_color.return_value = (80, 160, 255, 0)
    utcnow = utcnow + SCAN_INTERVAL
    async_fire_time_changed(hass, utcnow)
    await hass.async_block_till_done()

    state = hass.states.get("light.bedroom")
    assert state.state == STATE_ON
    assert dict(state.attributes) == {
        ATTR_FRIENDLY_NAME: "Bedroom",
        ATTR_SUPPORTED_COLOR_MODES: [ColorMode.RGBW],
        ATTR_SUPPORTED_FEATURES: 0,
        ATTR_COLOR_MODE: ColorMode.RGBW,
        ATTR_BRIGHTNESS: 255,
        ATTR_HS_COLOR: (pytest.approx(212.571), pytest.approx(68.627)),
        ATTR_RGB_COLOR: (80, 160, 255),
        ATTR_RGBW_COLOR: (80, 160, 255, 0),
        ATTR_XY_COLOR: (pytest.approx(0.17), pytest.approx(0.193)),
    }

    mock_light.get_color.side_effect = None
    mock_light.get_color.return_value = (80, 160, 200, 255)
    utcnow = utcnow + SCAN_INTERVAL
    async_fire_time_changed(hass, utcnow)
    await hass.async_block_till_done()

    state = hass.states.get("light.bedroom")
    assert state.state == STATE_ON
    assert dict(state.attributes) == {
        ATTR_FRIENDLY_NAME: "Bedroom",
        ATTR_SUPPORTED_COLOR_MODES: [ColorMode.RGBW],
        ATTR_SUPPORTED_FEATURES: 0,
        ATTR_COLOR_MODE: ColorMode.RGBW,
        ATTR_BRIGHTNESS: 255,
        ATTR_HS_COLOR: (pytest.approx(199.701), pytest.approx(26.275)),
        ATTR_RGB_COLOR: (188, 233, 255),
        ATTR_RGBW_COLOR: (80, 160, 200, 255),
        ATTR_XY_COLOR: (pytest.approx(0.259), pytest.approx(0.306)),
    }

    mock_light.get_color.side_effect = None
    mock_light.get_color.return_value = (80, 160, 200, 240)
    utcnow = utcnow + SCAN_INTERVAL
    async_fire_time_changed(hass, utcnow)
    await hass.async_block_till_done()

    state = hass.states.get("light.bedroom")
    assert state.state == STATE_ON
    assert dict(state.attributes) == {
        ATTR_FRIENDLY_NAME: "Bedroom",
        ATTR_SUPPORTED_COLOR_MODES: [ColorMode.RGBW],
        ATTR_SUPPORTED_FEATURES: 0,
        ATTR_COLOR_MODE: ColorMode.RGBW,
        ATTR_BRIGHTNESS: 240,
        ATTR_HS_COLOR: (pytest.approx(200.0), pytest.approx(27.059)),
        ATTR_RGB_COLOR: (186, 232, 255),
        ATTR_RGBW_COLOR: (85, 170, 212, 255),
        ATTR_XY_COLOR: (pytest.approx(0.257), pytest.approx(0.305)),
    }