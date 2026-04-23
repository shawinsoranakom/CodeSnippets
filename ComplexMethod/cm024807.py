def test_rgbww_to_color_temperature() -> None:
    """Test rgbww conversion to color temp.

    Temperature values must be in mireds
    Home Assistant uses rgbcw for rgbww
    """
    # Only cold channel enabled -> coldest color temperature
    assert color_util.rgbww_to_color_temperature((0, 0, 0, 255, 0), 2000, 6535) == (
        6535,
        255,
    )
    assert color_util.rgbww_to_color_temperature((0, 0, 0, 128, 0), 2000, 6535) == (
        6535,
        128,
    )
    # Only warm channel enabled -> warmest color temperature
    assert color_util.rgbww_to_color_temperature((0, 0, 0, 0, 255), 2000, 6535) == (
        2000,
        255,
    )
    assert color_util.rgbww_to_color_temperature((0, 0, 0, 0, 128), 2000, 6535) == (
        2000,
        128,
    )
    # More warm than cold channel enabled -> warmer than mid point
    assert color_util.rgbww_to_color_temperature((0, 0, 0, 112, 143), 2000, 6535) == (
        2876,
        255,
    )
    assert color_util.rgbww_to_color_temperature((0, 0, 0, 56, 72), 2000, 6535) == (
        2872,
        128,
    )
    # Both channels turned off -> warmest color temperature
    assert color_util.rgbww_to_color_temperature((0, 0, 0, 0, 0), 2000, 6535) == (
        2000,
        0,
    )