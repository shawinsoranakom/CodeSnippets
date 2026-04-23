def test_color_xy_to_hs() -> None:
    """Test color_xy_to_hs."""
    assert color_util.color_xy_to_hs(1, 1) == (47.294, 100)

    assert color_util.color_xy_to_hs(0.35, 0.35) == (38.182, 12.941)

    assert color_util.color_xy_to_hs(1, 0) == (345.882, 100)

    assert color_util.color_xy_to_hs(0, 1) == (120, 100)

    assert color_util.color_xy_to_hs(0, 0) == (225.176, 100)

    assert color_util.color_xy_to_hs(1, 0, GAMUT) == (359.294, 100)

    assert color_util.color_xy_to_hs(0, 1, GAMUT) == (100.706, 100)

    assert color_util.color_xy_to_hs(0, 0, GAMUT) == (221.463, 96.471)