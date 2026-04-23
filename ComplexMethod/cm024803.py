def test_color_rgbw_to_rgb() -> None:
    """Test color_rgbw_to_rgb."""
    assert color_util.color_rgbw_to_rgb(0, 0, 0, 0) == (0, 0, 0)

    assert color_util.color_rgbw_to_rgb(0, 0, 0, 255) == (255, 255, 255)

    assert color_util.color_rgbw_to_rgb(255, 0, 0, 0) == (255, 0, 0)

    assert color_util.color_rgbw_to_rgb(0, 255, 0, 0) == (0, 255, 0)

    assert color_util.color_rgbw_to_rgb(0, 0, 255, 0) == (0, 0, 255)

    assert color_util.color_rgbw_to_rgb(255, 127, 0, 0) == (255, 127, 0)

    assert color_util.color_rgbw_to_rgb(255, 0, 0, 253) == (255, 127, 127)

    assert color_util.color_rgbw_to_rgb(0, 0, 0, 127) == (127, 127, 127)