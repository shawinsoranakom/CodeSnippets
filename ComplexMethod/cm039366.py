def test_simple_imputer_keep_empty_features(strategy, array_type, keep_empty_features):
    """Check the behaviour of `keep_empty_features` with all strategies but
    'constant'.
    """
    X = np.array([[np.nan, 2], [np.nan, 3], [np.nan, 6]])
    X = _convert_container(X, array_type)
    imputer = SimpleImputer(strategy=strategy, keep_empty_features=keep_empty_features)

    for method in ["fit_transform", "transform"]:
        X_imputed = getattr(imputer, method)(X)
        if keep_empty_features:
            assert X_imputed.shape == X.shape
            if SCIPY_VERSION_BELOW_1_12 and array_type == "sparse":
                constant_feature = X_imputed[:, [0]].toarray()
            else:
                col0 = X_imputed[:, 0]
                constant_feature = col0.toarray() if array_type == "sparse" else col0
            assert_array_equal(constant_feature, 0)
        else:
            assert X_imputed.shape == (X.shape[0], X.shape[1] - 1)