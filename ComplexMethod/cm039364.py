def test_missing_indicator_new(
    missing_values, arr_type, dtype, param_features, n_features, features_indices
):
    X_fit = np.array([[missing_values, missing_values, 1], [4, 2, missing_values]])
    X_trans = np.array([[missing_values, missing_values, 1], [4, 12, 10]])
    X_fit_expected = np.array([[1, 1, 0], [0, 0, 1]])
    X_trans_expected = np.array([[1, 1, 0], [0, 0, 0]])

    # convert the input to the right array format and right dtype
    X_fit = arr_type(X_fit).astype(dtype)
    X_trans = arr_type(X_trans).astype(dtype)
    X_fit_expected = X_fit_expected.astype(dtype)
    X_trans_expected = X_trans_expected.astype(dtype)

    indicator = MissingIndicator(
        missing_values=missing_values, features=param_features, sparse=False
    )
    X_fit_mask = indicator.fit_transform(X_fit)
    X_trans_mask = indicator.transform(X_trans)

    assert X_fit_mask.shape[1] == n_features
    assert X_trans_mask.shape[1] == n_features

    assert_array_equal(indicator.features_, features_indices)
    assert_allclose(X_fit_mask, X_fit_expected[:, features_indices])
    assert_allclose(X_trans_mask, X_trans_expected[:, features_indices])

    assert X_fit_mask.dtype == bool
    assert X_trans_mask.dtype == bool
    assert isinstance(X_fit_mask, np.ndarray)
    assert isinstance(X_trans_mask, np.ndarray)

    indicator.set_params(sparse=True)
    X_fit_mask_sparse = indicator.fit_transform(X_fit)
    X_trans_mask_sparse = indicator.transform(X_trans)

    assert X_fit_mask_sparse.dtype == bool
    assert X_trans_mask_sparse.dtype == bool
    assert X_fit_mask_sparse.format == "csc"
    assert X_trans_mask_sparse.format == "csc"
    assert_allclose(X_fit_mask_sparse.toarray(), X_fit_mask)
    assert_allclose(X_trans_mask_sparse.toarray(), X_trans_mask)