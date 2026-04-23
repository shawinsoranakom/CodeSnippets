def test_white_levels_to_color_temperature() -> None:
    """Test warm, cold conversion to color temp.

    Temperature values must be in mireds
    Home Assistant uses rgbcw for rgbww
    """
    # Only cold channel enabled -> coldest color temperature
    assert color_util._white_levels_to_color_temperature(255, 0, 2000, 6535) == (
        6535,
        255,
    )
    assert color_util._white_levels_to_color_temperature(128, 0, 2000, 6535) == (
        6535,
        128,
    )
    # Only warm channel enabled -> warmest color temperature
    assert color_util._white_levels_to_color_temperature(0, 255, 2000, 6535) == (
        2000,
        255,
    )
    assert color_util._white_levels_to_color_temperature(0, 128, 2000, 6535) == (
        2000,
        128,
    )
    assert color_util._white_levels_to_color_temperature(112, 143, 2000, 6535) == (
        2876,
        255,
    )
    assert color_util._white_levels_to_color_temperature(56, 72, 2000, 6535) == (
        2872,
        128,
    )
    # Both channels turned off -> warmest color temperature
    assert color_util._white_levels_to_color_temperature(0, 0, 2000, 6535) == (
        2000,
        0,
    )