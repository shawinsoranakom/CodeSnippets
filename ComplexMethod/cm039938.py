def test_random_choice_csc(n_samples=10000, random_state=24):
    # Explicit class probabilities
    classes = [np.array([0, 1]), np.array([0, 1, 2])]
    class_probabilities = [np.array([0.5, 0.5]), np.array([0.6, 0.1, 0.3])]

    got = _random_choice_csc(n_samples, classes, class_probabilities, random_state)
    assert sp.issparse(got)

    for k in range(len(classes)):
        p = np.bincount(got[:, [k]].toarray().ravel()) / float(n_samples)
        assert_array_almost_equal(class_probabilities[k], p, decimal=1)

    # Implicit class probabilities
    classes = [[0, 1], [1, 2]]  # test for array-like support
    class_probabilities = [np.array([0.5, 0.5]), np.array([0, 1 / 2, 1 / 2])]

    got = _random_choice_csc(
        n_samples=n_samples, classes=classes, random_state=random_state
    )
    assert sp.issparse(got)

    for k in range(len(classes)):
        p = np.bincount(got[:, [k]].toarray().ravel()) / float(n_samples)
        assert_array_almost_equal(class_probabilities[k], p, decimal=1)

    # Edge case probabilities 1.0 and 0.0
    classes = [np.array([0, 1]), np.array([0, 1, 2])]
    class_probabilities = [np.array([0.0, 1.0]), np.array([0.0, 1.0, 0.0])]

    got = _random_choice_csc(n_samples, classes, class_probabilities, random_state)
    assert sp.issparse(got)

    for k in range(len(classes)):
        p = (
            np.bincount(
                got[:, [k]].toarray().ravel(), minlength=len(class_probabilities[k])
            )
            / n_samples
        )
        assert_array_almost_equal(class_probabilities[k], p, decimal=1)

    # One class target data
    classes = [[1], [0]]  # test for array-like support
    class_probabilities = [np.array([0.0, 1.0]), np.array([1.0])]

    got = _random_choice_csc(
        n_samples=n_samples, classes=classes, random_state=random_state
    )
    assert sp.issparse(got)

    for k in range(len(classes)):
        p = np.bincount(got[:, [k]].toarray().ravel()) / n_samples
        assert_array_almost_equal(class_probabilities[k], p, decimal=1)