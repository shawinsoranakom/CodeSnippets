def test_color_rgb_to_rgbw() -> None:
    """Test color_rgb_to_rgbw."""
    assert color_util.color_rgb_to_rgbw(0, 0, 0) == (0, 0, 0, 0)

    assert color_util.color_rgb_to_rgbw(255, 255, 255) == (0, 0, 0, 255)

    assert color_util.color_rgb_to_rgbw(255, 0, 0) == (255, 0, 0, 0)

    assert color_util.color_rgb_to_rgbw(0, 255, 0) == (0, 255, 0, 0)

    assert color_util.color_rgb_to_rgbw(0, 0, 255) == (0, 0, 255, 0)

    assert color_util.color_rgb_to_rgbw(255, 127, 0) == (255, 127, 0, 0)

    assert color_util.color_rgb_to_rgbw(255, 127, 127) == (255, 0, 0, 253)

    assert color_util.color_rgb_to_rgbw(127, 127, 127) == (0, 0, 0, 127)