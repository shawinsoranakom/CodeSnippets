def test_train_test_split(coo_container):
    X = np.arange(100).reshape((10, 10))
    X_s = coo_container(X)
    y = np.arange(10)

    # simple test
    split = train_test_split(X, y, test_size=None, train_size=0.5)
    X_train, X_test, y_train, y_test = split
    assert len(y_test) == len(y_train)
    # test correspondence of X and y
    assert_array_equal(X_train[:, 0], y_train * 10)
    assert_array_equal(X_test[:, 0], y_test * 10)

    # don't convert lists to anything else by default
    split = train_test_split(X, X_s, y.tolist())
    X_train, X_test, X_s_train, X_s_test, y_train, y_test = split
    assert isinstance(y_train, list)
    assert isinstance(y_test, list)

    # allow nd-arrays
    X_4d = np.arange(10 * 5 * 3 * 2).reshape(10, 5, 3, 2)
    y_3d = np.arange(10 * 7 * 11).reshape(10, 7, 11)
    split = train_test_split(X_4d, y_3d)
    assert split[0].shape == (7, 5, 3, 2)
    assert split[1].shape == (3, 5, 3, 2)
    assert split[2].shape == (7, 7, 11)
    assert split[3].shape == (3, 7, 11)

    # test stratification option
    y = np.array([1, 1, 1, 1, 2, 2, 2, 2])
    for test_size, exp_test_size in zip([2, 4, 0.25, 0.5, 0.75], [2, 4, 2, 4, 6]):
        train, test = train_test_split(
            y, test_size=test_size, stratify=y, random_state=0
        )
        assert len(test) == exp_test_size
        assert len(test) + len(train) == len(y)
        # check the 1:1 ratio of ones and twos in the data is preserved
        assert np.sum(train == 1) == np.sum(train == 2)

    # test unshuffled split
    y = np.arange(10)
    for test_size in [2, 0.2]:
        train, test = train_test_split(y, shuffle=False, test_size=test_size)
        assert_array_equal(test, [8, 9])
        assert_array_equal(train, [0, 1, 2, 3, 4, 5, 6, 7])