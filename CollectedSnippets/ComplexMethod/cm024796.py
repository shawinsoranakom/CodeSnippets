def test_color_RGB_to_xy() -> None:
    """Test color_RGB_to_xy."""
    assert color_util.color_RGB_to_xy(0, 0, 0) == (0, 0)
    assert color_util.color_RGB_to_xy(255, 255, 255) == (0.323, 0.329)

    assert color_util.color_RGB_to_xy(0, 0, 255) == (0.136, 0.04)

    assert color_util.color_RGB_to_xy(0, 255, 0) == (0.172, 0.747)

    assert color_util.color_RGB_to_xy(255, 0, 0) == (0.701, 0.299)

    assert color_util.color_RGB_to_xy(128, 0, 0) == (0.701, 0.299)

    assert color_util.color_RGB_to_xy(0, 0, 255, GAMUT) == (0.138, 0.08)

    assert color_util.color_RGB_to_xy(0, 255, 0, GAMUT) == (0.215, 0.711)

    assert color_util.color_RGB_to_xy(255, 0, 0, GAMUT) == (0.7, 0.299)