def test_perfect_matches(score_func):
    assert score_func([], []) == pytest.approx(1.0)
    assert score_func([0], [1]) == pytest.approx(1.0)
    assert score_func([0, 0, 0], [0, 0, 0]) == pytest.approx(1.0)
    assert score_func([0, 1, 0], [42, 7, 42]) == pytest.approx(1.0)
    assert score_func([0.0, 1.0, 0.0], [42.0, 7.0, 42.0]) == pytest.approx(1.0)
    assert score_func([0.0, 1.0, 2.0], [42.0, 7.0, 2.0]) == pytest.approx(1.0)
    assert score_func([0, 1, 2], [42, 7, 2]) == pytest.approx(1.0)