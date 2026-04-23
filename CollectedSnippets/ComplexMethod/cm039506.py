def test_perfect_matches_with_changing_means(score_func, average_method):
    assert score_func([], [], average_method=average_method) == pytest.approx(1.0)
    assert score_func([0], [1], average_method=average_method) == pytest.approx(1.0)
    assert score_func(
        [0, 0, 0], [0, 0, 0], average_method=average_method
    ) == pytest.approx(1.0)
    assert score_func(
        [0, 1, 0], [42, 7, 42], average_method=average_method
    ) == pytest.approx(1.0)
    assert score_func(
        [0.0, 1.0, 0.0], [42.0, 7.0, 42.0], average_method=average_method
    ) == pytest.approx(1.0)
    assert score_func(
        [0.0, 1.0, 2.0], [42.0, 7.0, 2.0], average_method=average_method
    ) == pytest.approx(1.0)
    assert score_func(
        [0, 1, 2], [42, 7, 2], average_method=average_method
    ) == pytest.approx(1.0)
    # Non-regression tests for: https://github.com/scikit-learn/scikit-learn/issues/30950
    assert score_func([0, 1], [0, 1], average_method=average_method) == pytest.approx(
        1.0
    )
    assert score_func(
        [0, 1, 2, 3], [0, 1, 2, 3], average_method=average_method
    ) == pytest.approx(1.0)