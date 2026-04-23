def check_regressors_train(
    name, regressor_orig, readonly_memmap=False, X_dtype=np.float64
):
    X, y = _regression_dataset()
    X = X.astype(X_dtype)
    y = scale(y)  # X is already scaled
    regressor = clone(regressor_orig)
    X = _enforce_estimator_tags_X(regressor, X)
    y = _enforce_estimator_tags_y(regressor, y)
    if name in CROSS_DECOMPOSITION:
        rnd = np.random.RandomState(0)
        y_ = np.vstack([y, 2 * y + rnd.randint(2, size=len(y))])
        y_ = y_.T
    else:
        y_ = y

    if readonly_memmap:
        X, y, y_ = create_memmap_backed_data([X, y, y_])

    if not hasattr(regressor, "alphas") and hasattr(regressor, "alpha"):
        # linear regressors need to set alpha, but not generalized CV ones
        regressor.alpha = 0.01
    if name == "PassiveAggressiveRegressor":
        regressor.C = 0.01

    # raises error on malformed input for fit
    with raises(
        ValueError,
        err_msg=(
            f"The classifier {name} does not raise an error when "
            "incorrect/malformed input data for fit is passed. The number of "
            "training examples is not the same as the number of labels. Perhaps "
            "use check_X_y in fit."
        ),
    ):
        regressor.fit(X, y[:-1])
    # fit
    set_random_state(regressor)
    regressor.fit(X, y_)
    regressor.fit(X.tolist(), y_.tolist())
    y_pred = regressor.predict(X)
    assert y_pred.shape == y_.shape

    # TODO: find out why PLS and CCA fail. RANSAC is random
    # and furthermore assumes the presence of outliers, hence
    # skipped
    if not get_tags(regressor).regressor_tags.poor_score:
        assert regressor.score(X, y_) > 0.5