def test_color_rgbww_to_rgb() -> None:
    """Test color_rgbww_to_rgb conversions."""
    assert color_util.color_rgbww_to_rgb(0, 54, 98, 255, 255, 2702, 6493) == (
        255,
        255,
        255,
    )
    # rgb fully on, + both white channels turned off -> rgb fully on
    assert color_util.color_rgbww_to_rgb(255, 255, 255, 0, 0, 2702, 6493) == (
        255,
        255,
        255,
    )
    # r < g < b + both white channels fully enabled -> r < g < b capped at 255
    assert color_util.color_rgbww_to_rgb(0, 118, 241, 255, 255, 2702, 6493) == (
        163,
        204,
        255,
    )
    # r < g < b + both white channels 50% enabled -> r < g < b capped at 128
    assert color_util.color_rgbww_to_rgb(0, 27, 49, 128, 128, 2702, 6493) == (
        128,
        128,
        128,
    )
    # r < g < b + both white channels 25% enabled -> r < g < b capped at 64
    assert color_util.color_rgbww_to_rgb(0, 14, 25, 64, 64, 2702, 6493) == (64, 64, 64)
    assert color_util.color_rgbww_to_rgb(9, 64, 0, 38, 38, 2702, 6493) == (32, 64, 16)
    assert color_util.color_rgbww_to_rgb(0, 0, 0, 0, 0, 2702, 6493) == (0, 0, 0)
    assert color_util.color_rgbww_to_rgb(103, 69, 0, 255, 255, 2702, 6535) == (
        255,
        193,
        112,
    )