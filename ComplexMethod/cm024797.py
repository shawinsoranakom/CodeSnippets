def test_color_xy_brightness_to_RGB() -> None:
    """Test color_xy_brightness_to_RGB."""
    assert color_util.color_xy_brightness_to_RGB(1, 1, 0) == (0, 0, 0)

    assert color_util.color_xy_brightness_to_RGB(0.35, 0.35, 128) == (194, 186, 169)

    assert color_util.color_xy_brightness_to_RGB(0.35, 0.35, 255) == (255, 243, 222)

    assert color_util.color_xy_brightness_to_RGB(1, 0, 255) == (255, 0, 60)

    assert color_util.color_xy_brightness_to_RGB(0, 1, 255) == (0, 255, 0)

    assert color_util.color_xy_brightness_to_RGB(0, 0, 255) == (0, 63, 255)

    assert color_util.color_xy_brightness_to_RGB(1, 0, 255, GAMUT) == (255, 0, 3)

    assert color_util.color_xy_brightness_to_RGB(0, 1, 255, GAMUT) == (82, 255, 0)

    assert color_util.color_xy_brightness_to_RGB(0, 0, 255, GAMUT) == (9, 85, 255)