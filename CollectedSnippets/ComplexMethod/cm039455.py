def test_importances(dtype, name, criterion):
    tolerance = 0.01
    if name in FOREST_REGRESSORS and criterion == "absolute_error":
        tolerance = 0.05

    # cast as dtype
    X = X_large.astype(dtype, copy=False)
    y = y_large.astype(dtype, copy=False)

    ForestEstimator = FOREST_ESTIMATORS[name]

    est = ForestEstimator(n_estimators=10, criterion=criterion, random_state=0)
    est.fit(X, y)
    importances = est.feature_importances_

    # The forest estimator can detect that only the first 3 features of the
    # dataset are informative:
    n_important = np.sum(importances > 0.1)
    assert importances.shape[0] == 10
    assert n_important == 3
    assert np.all(importances[:3] > 0.1)

    # Check with parallel
    importances = est.feature_importances_
    est.set_params(n_jobs=2)
    importances_parallel = est.feature_importances_
    assert_array_almost_equal(importances, importances_parallel)

    # Check with sample weights
    sample_weight = check_random_state(0).randint(1, 10, len(X))
    est = ForestEstimator(n_estimators=10, random_state=0, criterion=criterion)
    est.fit(X, y, sample_weight=sample_weight)
    importances = est.feature_importances_
    assert np.all(importances >= 0.0)

    for scale in [0.5, 100]:
        est = ForestEstimator(n_estimators=10, random_state=0, criterion=criterion)
        est.fit(X, y, sample_weight=scale * sample_weight)
        importances_bis = est.feature_importances_
        assert np.abs(importances - importances_bis).mean() < tolerance