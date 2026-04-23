def test_color_rgb_to_rgbww() -> None:
    """Test color_rgb_to_rgbww conversions."""
    # Light with mid point at ~4600K (warm white) -> output compensated by adding blue
    assert color_util.color_rgb_to_rgbww(255, 255, 255, 2702, 6493) == (
        0,
        54,
        98,
        255,
        255,
    )
    # Light with mid point at ~5500K (less warm white) -> output compensated by adding less blue
    assert color_util.color_rgb_to_rgbww(255, 255, 255, 1000, 10000) == (
        255,
        255,
        255,
        0,
        0,
    )
    # Light with mid point at ~1MK (unrealistically cold white) -> output compensated by adding red
    assert color_util.color_rgb_to_rgbww(255, 255, 255, 1000, 1000000) == (
        0,
        118,
        241,
        255,
        255,
    )
    assert color_util.color_rgb_to_rgbww(128, 128, 128, 2702, 6493) == (
        0,
        27,
        49,
        128,
        128,
    )
    assert color_util.color_rgb_to_rgbww(64, 64, 64, 2702, 6493) == (0, 14, 25, 64, 64)
    assert color_util.color_rgb_to_rgbww(32, 64, 16, 2702, 6493) == (9, 64, 0, 38, 38)
    assert color_util.color_rgb_to_rgbww(0, 0, 0, 2702, 6493) == (0, 0, 0, 0, 0)
    assert color_util.color_rgb_to_rgbww(0, 0, 0, 10000, 1000000) == (0, 0, 0, 0, 0)
    assert color_util.color_rgb_to_rgbww(255, 255, 255, 200000, 1000000) == (
        103,
        69,
        0,
        255,
        255,
    )