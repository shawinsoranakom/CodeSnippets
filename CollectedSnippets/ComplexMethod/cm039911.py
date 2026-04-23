def check_n_features_in_after_fitting(name, estimator_orig):
    # Make sure that n_features_in are checked after fitting
    tags = get_tags(estimator_orig)

    is_supported_X_types = tags.input_tags.two_d_array or tags.input_tags.categorical

    if not is_supported_X_types or tags.no_validation:
        return

    rng = np.random.RandomState(0)

    estimator = clone(estimator_orig)
    set_random_state(estimator)
    if "warm_start" in estimator.get_params():
        estimator.set_params(warm_start=False)

    n_samples = 15
    X = rng.normal(size=(n_samples, 4))
    X = _enforce_estimator_tags_X(estimator, X)

    if is_regressor(estimator):
        y = rng.normal(size=n_samples)
    else:
        y = rng.permutation(np.repeat(np.arange(3), 5))
    y = _enforce_estimator_tags_y(estimator, y)

    err_msg = (
        "`{name}.fit()` does not set the `n_features_in_` attribute. "
        "You might want to use `sklearn.utils.validation.validate_data` instead "
        "of `check_array` in `{name}.fit()` which takes care of setting the "
        "attribute.".format(name=name)
    )

    estimator.fit(X, y)
    assert hasattr(estimator, "n_features_in_"), err_msg
    assert estimator.n_features_in_ == X.shape[1], err_msg

    # check methods will check n_features_in_
    check_methods = [
        "predict",
        "transform",
        "decision_function",
        "predict_proba",
        "score",
    ]
    X_bad = X[:, [1]]

    err_msg = """\
        `{name}.{method}()` does not check for consistency between input number
        of features with {name}.fit(), via the `n_features_in_` attribute.
        You might want to use `sklearn.utils.validation.validate_data` instead
        of `check_array` in `{name}.fit()` and {name}.{method}()`. This can be done
        like the following:
        from sklearn.utils.validation import validate_data
        ...
        class MyEstimator(BaseEstimator):
            ...
            def fit(self, X, y):
                X, y = validate_data(self, X, y, ...)
                ...
                return self
            ...
            def {method}(self, X):
                X = validate_data(self, X, ..., reset=False)
                ...
            return X
    """
    err_msg = textwrap.dedent(err_msg)

    msg = f"X has 1 features, but \\w+ is expecting {X.shape[1]} features as input"
    for method in check_methods:
        if not hasattr(estimator, method):
            continue

        callable_method = getattr(estimator, method)
        if method == "score":
            callable_method = partial(callable_method, y=y)

        with raises(
            ValueError, match=msg, err_msg=err_msg.format(name=name, method=method)
        ):
            callable_method(X_bad)

    # partial_fit will check in the second call
    if not hasattr(estimator, "partial_fit"):
        return

    estimator = clone(estimator_orig)
    if is_classifier(estimator):
        estimator.partial_fit(X, y, classes=np.unique(y))
    else:
        estimator.partial_fit(X, y)
    assert estimator.n_features_in_ == X.shape[1]

    with raises(ValueError, match=msg):
        estimator.partial_fit(X_bad, y)