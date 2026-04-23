def test_match_max_scale() -> None:
    """Test match_max_scale."""
    match_max_scale = color_util.match_max_scale
    assert match_max_scale((255, 255, 255), (255, 255, 255)) == (255, 255, 255)
    assert match_max_scale((0, 0, 0), (0, 0, 0)) == (0, 0, 0)
    assert match_max_scale((255, 255, 255), (128, 128, 128)) == (255, 255, 255)
    assert match_max_scale((0, 255, 0), (64, 128, 128)) == (128, 255, 255)
    assert match_max_scale((0, 100, 0), (128, 64, 64)) == (100, 50, 50)
    assert match_max_scale((10, 20, 33), (100, 200, 333)) == (10, 20, 33)
    assert match_max_scale((255,), (100, 200, 333)) == (77, 153, 255)
    assert match_max_scale((128,), (10.5, 20.9, 30.4)) == (44, 88, 128)
    assert match_max_scale((10, 20, 30, 128), (100, 200, 333)) == (38, 77, 128)