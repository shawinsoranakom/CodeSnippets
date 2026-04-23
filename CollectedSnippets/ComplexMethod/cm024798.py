def test_color_xy_to_RGB() -> None:
    """Test color_xy_to_RGB."""
    assert color_util.color_xy_to_RGB(0.35, 0.35) == (255, 243, 222)

    assert color_util.color_xy_to_RGB(1, 0) == (255, 0, 60)

    assert color_util.color_xy_to_RGB(0, 1) == (0, 255, 0)

    assert color_util.color_xy_to_RGB(0, 0) == (0, 63, 255)

    assert color_util.color_xy_to_RGB(1, 0, GAMUT) == (255, 0, 3)

    assert color_util.color_xy_to_RGB(0, 1, GAMUT) == (82, 255, 0)

    assert color_util.color_xy_to_RGB(0, 0, GAMUT) == (9, 85, 255)