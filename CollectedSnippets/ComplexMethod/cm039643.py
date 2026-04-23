def test_inplace_data_preprocessing(sparse_container, use_sw, global_random_seed):
    # Check that the data is not modified inplace by the linear regression
    # estimator.
    rng = np.random.RandomState(global_random_seed)
    original_X_data = rng.randn(10, 12)
    original_y_data = rng.randn(10, 2)
    orginal_sw_data = rng.rand(10)

    if sparse_container is not None:
        X = sparse_container(original_X_data)
    else:
        X = original_X_data.copy()
    y = original_y_data.copy()
    # XXX: Note hat y_sparse is not supported (broken?) in the current
    # implementation of LinearRegression.

    if use_sw:
        sample_weight = orginal_sw_data.copy()
    else:
        sample_weight = None

    # Do not allow inplace preprocessing of X and y:
    reg = LinearRegression()
    reg.fit(X, y, sample_weight=sample_weight)
    if sparse_container is not None:
        assert_allclose(X.toarray(), original_X_data)
    else:
        assert_allclose(X, original_X_data)
    assert_allclose(y, original_y_data)

    if use_sw:
        assert_allclose(sample_weight, orginal_sw_data)

    # Allow inplace preprocessing of X and y
    reg = LinearRegression(copy_X=False)
    reg.fit(X, y, sample_weight=sample_weight)
    if sparse_container is not None:
        # No optimization relying on the inplace modification of sparse input
        # data has been implemented at this time.
        assert_allclose(X.toarray(), original_X_data)
    else:
        # X has been offset (and optionally rescaled by sample weights)
        # inplace. The 0.42 threshold is arbitrary and has been found to be
        # robust to any random seed in the admissible range.
        assert np.linalg.norm(X - original_X_data) > 0.42

    # y should not have been modified inplace by LinearRegression.fit.
    assert_allclose(y, original_y_data)

    if use_sw:
        # Sample weights have no reason to ever be modified inplace.
        assert_allclose(sample_weight, orginal_sw_data)