def check_outliers_train(name, estimator_orig, readonly_memmap=True):
    n_samples = 300
    X, _ = make_blobs(n_samples=n_samples, random_state=0)
    X = shuffle(X, random_state=7)

    if readonly_memmap:
        X = create_memmap_backed_data(X)

    n_samples, n_features = X.shape
    estimator = clone(estimator_orig)
    set_random_state(estimator)

    # fit
    estimator.fit(X)
    # with lists
    estimator.fit(X.tolist())

    y_pred = estimator.predict(X)
    assert y_pred.shape == (n_samples,)
    assert y_pred.dtype.kind == "i"
    assert_array_equal(np.unique(y_pred), np.array([-1, 1]))

    decision = estimator.decision_function(X)
    scores = estimator.score_samples(X)
    for output in [decision, scores]:
        assert output.dtype == np.dtype("float")
        assert output.shape == (n_samples,)

    # raises error on malformed input for predict
    with raises(ValueError):
        estimator.predict(X.T)

    # decision_function agrees with predict
    dec_pred = (decision >= 0).astype(int)
    dec_pred[dec_pred == 0] = -1
    assert_array_equal(dec_pred, y_pred)

    # raises error on malformed input for decision_function
    with raises(ValueError):
        estimator.decision_function(X.T)

    # decision_function is a translation of score_samples
    y_dec = scores - estimator.offset_
    assert_allclose(y_dec, decision)

    # raises error on malformed input for score_samples
    with raises(ValueError):
        estimator.score_samples(X.T)

    # contamination parameter (not for OneClassSVM which has the nu parameter)
    if hasattr(estimator, "contamination") and not hasattr(estimator, "novelty"):
        # proportion of outliers equal to contamination parameter when not
        # set to 'auto'. This is true for the training set and cannot thus be
        # checked as follows for estimators with a novelty parameter such as
        # LocalOutlierFactor (tested in check_outliers_fit_predict)
        expected_outliers = 30
        contamination = expected_outliers / n_samples
        estimator.set_params(contamination=contamination)
        estimator.fit(X)
        y_pred = estimator.predict(X)

        num_outliers = np.sum(y_pred != 1)
        # num_outliers should be equal to expected_outliers unless
        # there are ties in the decision_function values. this can
        # only be tested for estimators with a decision_function
        # method, i.e. all estimators except LOF which is already
        # excluded from this if branch.
        if num_outliers != expected_outliers:
            decision = estimator.decision_function(X)
            check_outlier_corruption(num_outliers, expected_outliers, decision)