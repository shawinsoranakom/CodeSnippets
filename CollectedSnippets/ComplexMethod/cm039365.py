def test_missing_indicator_sparse_param(arr_type, missing_values, param_sparse):
    # check the format of the output with different sparse parameter
    X_fit = np.array([[missing_values, missing_values, 1], [4, missing_values, 2]])
    X_trans = np.array([[missing_values, missing_values, 1], [4, 12, 10]])
    X_fit = arr_type(X_fit).astype(np.float64)
    X_trans = arr_type(X_trans).astype(np.float64)

    indicator = MissingIndicator(missing_values=missing_values, sparse=param_sparse)
    X_fit_mask = indicator.fit_transform(X_fit)
    X_trans_mask = indicator.transform(X_trans)

    if param_sparse is True:
        assert X_fit_mask.format == "csc"
        assert X_trans_mask.format == "csc"
    elif param_sparse == "auto" and missing_values == 0:
        assert isinstance(X_fit_mask, np.ndarray)
        assert isinstance(X_trans_mask, np.ndarray)
    elif param_sparse is False:
        assert isinstance(X_fit_mask, np.ndarray)
        assert isinstance(X_trans_mask, np.ndarray)
    else:
        if sparse.issparse(X_fit):
            assert X_fit_mask.format == "csc"
            assert X_trans_mask.format == "csc"
        else:
            assert isinstance(X_fit_mask, np.ndarray)
            assert isinstance(X_trans_mask, np.ndarray)