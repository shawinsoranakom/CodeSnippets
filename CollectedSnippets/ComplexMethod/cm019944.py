def test_filter_supported_color_modes() -> None:
    """Test filter_supported_color_modes."""
    supported = {light.ColorMode.HS}
    assert light.filter_supported_color_modes(supported) == supported

    # Supported color modes must not be empty
    supported = set()
    with pytest.raises(HomeAssistantError):
        light.filter_supported_color_modes(supported)

    # ColorMode.WHITE must be combined with a color mode supporting color
    supported = {light.ColorMode.WHITE}
    with pytest.raises(HomeAssistantError):
        light.filter_supported_color_modes(supported)

    supported = {light.ColorMode.WHITE, light.ColorMode.COLOR_TEMP}
    with pytest.raises(HomeAssistantError):
        light.filter_supported_color_modes(supported)

    supported = {light.ColorMode.WHITE, light.ColorMode.HS}
    assert light.filter_supported_color_modes(supported) == supported

    # ColorMode.ONOFF will be removed if combined with other modes
    supported = {light.ColorMode.ONOFF}
    assert light.filter_supported_color_modes(supported) == supported

    supported = {light.ColorMode.ONOFF, light.ColorMode.COLOR_TEMP}
    assert light.filter_supported_color_modes(supported) == {light.ColorMode.COLOR_TEMP}

    # ColorMode.BRIGHTNESS will be removed if combined with other modes
    supported = {light.ColorMode.BRIGHTNESS}
    assert light.filter_supported_color_modes(supported) == supported

    supported = {light.ColorMode.BRIGHTNESS, light.ColorMode.COLOR_TEMP}
    assert light.filter_supported_color_modes(supported) == {light.ColorMode.COLOR_TEMP}

    # ColorMode.BRIGHTNESS has priority over ColorMode.ONOFF
    supported = {light.ColorMode.ONOFF, light.ColorMode.BRIGHTNESS}
    assert light.filter_supported_color_modes(supported) == {light.ColorMode.BRIGHTNESS}