def _enforce_estimator_tags_X(estimator, X, X_test=None, kernel=linear_kernel):
    # Estimators with `1darray` in `X_types` tag only accept
    # X of shape (`n_samples`,)
    if get_tags(estimator).input_tags.one_d_array:
        X = X[:, 0]
        if X_test is not None:
            X_test = X_test[:, 0]  # pragma: no cover
    # Estimators with a `requires_positive_X` tag only accept
    # strictly positive data
    if get_tags(estimator).input_tags.positive_only:
        X = X - X.min()
        if X_test is not None:
            X_test = X_test - X_test.min()  # pragma: no cover
    if get_tags(estimator).input_tags.categorical:
        dtype = np.float64 if get_tags(estimator).input_tags.allow_nan else np.int32
        X = np.round((X - X.min())).astype(dtype)
        if X_test is not None:
            X_test = np.round((X_test - X_test.min())).astype(dtype)  # pragma: no cover

    if estimator.__class__.__name__ == "SkewedChi2Sampler":
        # SkewedChi2Sampler requires X > -skewdness in transform
        X = X - X.min()
        if X_test is not None:
            X_test = X_test - X_test.min()  # pragma: no cover

    X_res = X

    # Pairwise estimators only accept
    # X of shape (`n_samples`, `n_samples`)
    if _is_pairwise_metric(estimator):
        X_res = pairwise_distances(X, metric="euclidean")
        if X_test is not None:
            X_test = pairwise_distances(
                X_test, X, metric="euclidean"
            )  # pragma: no cover
    elif get_tags(estimator).input_tags.pairwise:
        X_res = kernel(X, X)
        if X_test is not None:
            X_test = kernel(X_test, X)  # pragma: no cover
    if X_test is not None:
        return X_res, X_test
    return X_res