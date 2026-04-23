def test_color_RGB_to_xy_brightness() -> None:
    """Test color_RGB_to_xy_brightness."""
    assert color_util.color_RGB_to_xy_brightness(0, 0, 0) == (0, 0, 0)
    assert color_util.color_RGB_to_xy_brightness(255, 255, 255) == (0.323, 0.329, 255)

    assert color_util.color_RGB_to_xy_brightness(0, 0, 255) == (0.136, 0.04, 12)

    assert color_util.color_RGB_to_xy_brightness(0, 255, 0) == (0.172, 0.747, 170)

    assert color_util.color_RGB_to_xy_brightness(255, 0, 0) == (0.701, 0.299, 72)

    assert color_util.color_RGB_to_xy_brightness(128, 0, 0) == (0.701, 0.299, 16)

    assert color_util.color_RGB_to_xy_brightness(255, 0, 0, GAMUT) == (0.7, 0.299, 72)

    assert color_util.color_RGB_to_xy_brightness(0, 255, 0, GAMUT) == (
        0.215,
        0.711,
        170,
    )

    assert color_util.color_RGB_to_xy_brightness(0, 0, 255, GAMUT) == (0.138, 0.08, 12)