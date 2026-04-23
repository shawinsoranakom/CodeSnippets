def test_ransac_dynamic_max_trials():
    # Numbers hand-calculated and confirmed on page 119 (Table 4.3) in
    #   Hartley, R.~I. and Zisserman, A., 2004,
    #   Multiple View Geometry in Computer Vision, Second Edition,
    #   Cambridge University Press, ISBN: 0521540518

    # e = 0%, min_samples = X
    assert _dynamic_max_trials(100, 100, 2, 0.99) == 1

    # e = 5%, min_samples = 2
    assert _dynamic_max_trials(95, 100, 2, 0.99) == 2
    # e = 10%, min_samples = 2
    assert _dynamic_max_trials(90, 100, 2, 0.99) == 3
    # e = 30%, min_samples = 2
    assert _dynamic_max_trials(70, 100, 2, 0.99) == 7
    # e = 50%, min_samples = 2
    assert _dynamic_max_trials(50, 100, 2, 0.99) == 17

    # e = 5%, min_samples = 8
    assert _dynamic_max_trials(95, 100, 8, 0.99) == 5
    # e = 10%, min_samples = 8
    assert _dynamic_max_trials(90, 100, 8, 0.99) == 9
    # e = 30%, min_samples = 8
    assert _dynamic_max_trials(70, 100, 8, 0.99) == 78
    # e = 50%, min_samples = 8
    assert _dynamic_max_trials(50, 100, 8, 0.99) == 1177

    # e = 0%, min_samples = 10
    assert _dynamic_max_trials(1, 100, 10, 0) == 0
    assert _dynamic_max_trials(1, 100, 10, 1) == float("inf")