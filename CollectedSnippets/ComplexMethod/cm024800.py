def test_color_hs_to_xy() -> None:
    """Test color_hs_to_xy."""
    assert color_util.color_hs_to_xy(180, 100) == (0.151, 0.343)

    assert color_util.color_hs_to_xy(350, 12.5) == (0.356, 0.321)

    assert color_util.color_hs_to_xy(140, 50) == (0.23, 0.474)

    assert color_util.color_hs_to_xy(0, 40) == (0.474, 0.317)

    assert color_util.color_hs_to_xy(360, 0) == (0.323, 0.329)

    assert color_util.color_hs_to_xy(0, 100, GAMUT) == (0.7, 0.299)

    assert color_util.color_hs_to_xy(120, 100, GAMUT) == (0.215, 0.711)

    assert color_util.color_hs_to_xy(180, 100, GAMUT) == (0.17, 0.34)

    assert color_util.color_hs_to_xy(240, 100, GAMUT) == (0.138, 0.08)

    assert color_util.color_hs_to_xy(360, 100, GAMUT) == (0.7, 0.299)