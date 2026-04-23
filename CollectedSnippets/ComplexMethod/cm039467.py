def test_iforest_with_uniform_data():
    """Test whether iforest predicts inliers when using uniform data"""

    # 2-d array of all 1s
    X = np.ones((100, 10))
    iforest = IsolationForest()
    iforest.fit(X)

    rng = np.random.RandomState(0)

    assert all(iforest.predict(X) == 1)
    assert all(iforest.predict(rng.randn(100, 10)) == 1)
    assert all(iforest.predict(X + 1) == 1)
    assert all(iforest.predict(X - 1) == 1)

    # 2-d array where columns contain the same value across rows
    X = np.repeat(rng.randn(1, 10), 100, 0)
    iforest = IsolationForest()
    iforest.fit(X)

    assert all(iforest.predict(X) == 1)
    assert all(iforest.predict(rng.randn(100, 10)) == 1)
    assert all(iforest.predict(np.ones((100, 10))) == 1)

    # Single row
    X = rng.randn(1, 10)
    iforest = IsolationForest()
    iforest.fit(X)

    assert all(iforest.predict(X) == 1)
    assert all(iforest.predict(rng.randn(100, 10)) == 1)
    assert all(iforest.predict(np.ones((100, 10))) == 1)