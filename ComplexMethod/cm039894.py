def _check_estimator_sparse_container(name, estimator_orig, sparse_type):
    rng = np.random.RandomState(0)
    X = rng.uniform(size=(40, 3))
    X[X < 0.6] = 0
    X = _enforce_estimator_tags_X(estimator_orig, X)
    y = (4 * rng.uniform(size=X.shape[0])).astype(np.int32)
    # catch deprecation warnings
    with ignore_warnings(category=FutureWarning):
        estimator = clone(estimator_orig)
    y = _enforce_estimator_tags_y(estimator, y)
    tags = get_tags(estimator_orig)
    for matrix_format, X in _generate_sparse_data(sparse_type(X)):
        # catch deprecation warnings
        with ignore_warnings(category=FutureWarning):
            estimator = clone(estimator_orig)
            if name in ["Scaler", "StandardScaler"]:
                estimator.set_params(with_mean=False)
        # fit and predict
        if "64" in matrix_format:
            err_msg = (
                f"Estimator {name} doesn't seem to support {matrix_format} "
                "matrix, and is not failing gracefully, e.g. by using "
                "check_array(X, accept_large_sparse=False)."
            )
        else:
            err_msg = (
                f"Estimator {name} doesn't seem to fail gracefully on sparse "
                "data: error message should state explicitly that sparse "
                "input is not supported if this is not the case, e.g. by using "
                "check_array(X, accept_sparse=False)."
            )
        with raises(
            (TypeError, ValueError),
            match=["sparse", "Sparse"],
            may_pass=True,
            err_msg=err_msg,
        ):
            with ignore_warnings(category=FutureWarning):
                estimator.fit(X, y)
            if hasattr(estimator, "predict"):
                pred = estimator.predict(X)
                if tags.target_tags.multi_output and not tags.target_tags.single_output:
                    assert pred.shape == (X.shape[0], 1)
                else:
                    assert pred.shape == (X.shape[0],)
            if hasattr(estimator, "predict_proba"):
                probs = estimator.predict_proba(X)
                if not tags.classifier_tags.multi_class:
                    expected_probs_shape = (X.shape[0], 2)
                else:
                    expected_probs_shape = (X.shape[0], 4)
                assert probs.shape == expected_probs_shape