def test_chi_square_kernel():
    rng = np.random.RandomState(0)
    X = rng.random_sample((5, 4))
    Y = rng.random_sample((10, 4))
    K_add = additive_chi2_kernel(X, Y)
    gamma = 0.1
    K = chi2_kernel(X, Y, gamma=gamma)
    assert K.dtype == float
    for i, x in enumerate(X):
        for j, y in enumerate(Y):
            chi2 = -np.sum((x - y) ** 2 / (x + y))
            chi2_exp = np.exp(gamma * chi2)
            assert_almost_equal(K_add[i, j], chi2)
            assert_almost_equal(K[i, j], chi2_exp)

    # check diagonal is ones for data with itself
    K = chi2_kernel(Y)
    assert_array_equal(np.diag(K), 1)
    # check off-diagonal is < 1 but > 0:
    assert np.all(K > 0)
    assert np.all(K - np.diag(np.diag(K)) < 1)
    # check that float32 is preserved
    X = rng.random_sample((5, 4)).astype(np.float32)
    Y = rng.random_sample((10, 4)).astype(np.float32)
    K = chi2_kernel(X, Y)
    assert K.dtype == np.float32

    # check integer type gets converted,
    # check that zeros are handled
    X = rng.random_sample((10, 4)).astype(np.int32)
    K = chi2_kernel(X, X)
    assert np.isfinite(K).all()
    assert K.dtype == float

    # check that kernel of similar things is greater than dissimilar ones
    X = [[0.3, 0.7], [1.0, 0]]
    Y = [[0, 1], [0.9, 0.1]]
    K = chi2_kernel(X, Y)
    assert K[0, 0] > K[0, 1]
    assert K[1, 1] > K[1, 0]

    # test negative input
    with pytest.raises(ValueError):
        chi2_kernel([[0, -1]])
    with pytest.raises(ValueError):
        chi2_kernel([[0, -1]], [[-1, -1]])
    with pytest.raises(ValueError):
        chi2_kernel([[0, 1]], [[-1, -1]])

    # different n_features in X and Y
    with pytest.raises(ValueError):
        chi2_kernel([[0, 1]], [[0.2, 0.2, 0.6]])