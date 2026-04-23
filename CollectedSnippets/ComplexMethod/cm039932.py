def test_bruteforce_ellipsis():
    # Check that the bruteforce ellipsis (used when the number of non-blank
    # characters exceeds N_CHAR_MAX) renders correctly.

    lr = LogisticRegression()

    # test when the left and right side of the ellipsis aren't on the same
    # line.
    expected = """
LogisticRegression(C=1.0, class_weight=None, dual=False, fit_intercept=True,
                   in...
                   multi_class='warn', n_jobs=None, random_state=None,
                   solver='warn', tol=0.0001, verbose=0, warm_start=False)"""

    expected = expected[1:]  # remove first \n
    assert lr.__repr__(N_CHAR_MAX=150) == expected

    # test with very small N_CHAR_MAX
    # Note that N_CHAR_MAX is not strictly enforced, but it's normal: to avoid
    # weird reprs we still keep the whole line of the right part (after the
    # ellipsis).
    expected = """
Lo...
                   solver='warn', tol=0.0001, verbose=0, warm_start=False)"""

    expected = expected[1:]  # remove first \n
    assert lr.__repr__(N_CHAR_MAX=4) == expected

    # test with N_CHAR_MAX == number of non-blank characters: In this case we
    # don't want ellipsis
    full_repr = lr.__repr__(N_CHAR_MAX=float("inf"))
    n_nonblank = len("".join(full_repr.split()))
    assert lr.__repr__(N_CHAR_MAX=n_nonblank) == full_repr
    assert "..." not in full_repr

    # test with N_CHAR_MAX == number of non-blank characters - 10: the left and
    # right side of the ellispsis are on different lines. In this case we
    # want to expend the whole line of the right side
    expected = """
LogisticRegression(C=1.0, class_weight=None, dual=False, fit_intercept=True,
                   intercept_scaling=1, l1_ratio=0,...00,
                   multi_class='warn', n_jobs=None, random_state=None,
                   solver='warn', tol=0.0001, verbose=0, warm_start=False)"""
    expected = expected[1:]  # remove first \n
    assert lr.__repr__(N_CHAR_MAX=n_nonblank - 10) == expected

    # test with N_CHAR_MAX == number of non-blank characters - 10: the left and
    # right side of the ellispsis are on the same line. In this case we don't
    # want to expend the whole line of the right side, just add the ellispsis
    # between the 2 sides.
    expected = """
LogisticRegression(C=1.0, class_weight=None, dual=False, fit_intercept=True,
                   intercept_scaling=1, l1_ratio=0, max...r=100,
                   multi_class='warn', n_jobs=None, random_state=None,
                   solver='warn', tol=0.0001, verbose=0, warm_start=False)"""
    expected = expected[1:]  # remove first \n
    assert lr.__repr__(N_CHAR_MAX=n_nonblank - 4) == expected

    # test with N_CHAR_MAX == number of non-blank characters - 2: the left and
    # right side of the ellispsis are on the same line, but adding the ellipsis
    # would actually make the repr longer. So we don't add the ellipsis.
    expected = """
LogisticRegression(C=1.0, class_weight=None, dual=False, fit_intercept=True,
                   intercept_scaling=1, l1_ratio=0, max_iter=100,
                   multi_class='warn', n_jobs=None, random_state=None,
                   solver='warn', tol=0.0001, verbose=0, warm_start=False)"""
    expected = expected[1:]  # remove first \n
    assert lr.__repr__(N_CHAR_MAX=n_nonblank - 2) == expected