def check_estimators_pickle(name, estimator_orig, readonly_memmap=False):
    """Test that we can pickle all estimators."""
    check_methods = ["predict", "transform", "decision_function", "predict_proba"]

    X, y = make_blobs(
        n_samples=30,
        centers=[[0, 0, 0], [1, 1, 1]],
        random_state=0,
        n_features=2,
        cluster_std=0.1,
    )

    X = _enforce_estimator_tags_X(estimator_orig, X, kernel=rbf_kernel)

    tags = get_tags(estimator_orig)
    # include NaN values when the estimator should deal with them
    if tags.input_tags.allow_nan:
        # set randomly 10 elements to np.nan
        rng = np.random.RandomState(42)
        mask = rng.choice(X.size, 10, replace=False)
        X.reshape(-1)[mask] = np.nan

    estimator = clone(estimator_orig)

    y = _enforce_estimator_tags_y(estimator, y)

    set_random_state(estimator)
    estimator.fit(X, y)

    if readonly_memmap:
        unpickled_estimator = create_memmap_backed_data(estimator)
    else:
        # No need to touch the file system in that case.
        pickled_estimator = pickle.dumps(estimator)
        module_name = estimator.__module__
        if module_name.startswith("sklearn.") and not (
            "test_" in module_name or module_name.endswith("_testing")
        ):
            # strict check for sklearn estimators that are not implemented in test
            # modules.
            assert b"_sklearn_version" in pickled_estimator
        unpickled_estimator = pickle.loads(pickled_estimator)

    result = dict()
    for method in check_methods:
        if hasattr(estimator, method):
            result[method] = getattr(estimator, method)(X)

    for method in result:
        unpickled_result = getattr(unpickled_estimator, method)(X)
        assert_allclose_dense_sparse(result[method], unpickled_result)