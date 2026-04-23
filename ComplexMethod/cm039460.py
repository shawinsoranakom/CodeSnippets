def test_estimators_samples(ForestClass, bootstrap, seed):
    """Estimators_samples_ property should be consistent.

    Tests consistency across fits and whether or not the seed for the random generator
    is set.
    """
    X, y = make_hastie_10_2(n_samples=200, random_state=1)

    if bootstrap:
        max_samples = 0.5
    else:
        max_samples = None
    est = ForestClass(
        n_estimators=10,
        max_samples=max_samples,
        max_features=0.5,
        random_state=seed,
        bootstrap=bootstrap,
    )
    est.fit(X, y)

    estimators_samples = est.estimators_samples_.copy()

    # Test repeated calls result in same set of indices
    assert_array_equal(estimators_samples, est.estimators_samples_)
    estimators = est.estimators_

    assert isinstance(estimators_samples, list)
    assert len(estimators_samples) == len(estimators)
    assert estimators_samples[0].dtype == np.int32

    for i in range(len(estimators)):
        if bootstrap:
            assert len(estimators_samples[i]) == len(X) // 2

            # the bootstrap should be a resampling with replacement
            assert len(np.unique(estimators_samples[i])) < len(estimators_samples[i])
        else:
            assert len(set(estimators_samples[i])) == len(X)

    estimator_index = 0
    estimator_samples = estimators_samples[estimator_index]
    estimator = estimators[estimator_index]

    X_train = X[estimator_samples]
    y_train = y[estimator_samples]

    orig_tree_values = estimator.tree_.value
    estimator = clone(estimator)
    estimator.fit(X_train, y_train)
    new_tree_values = estimator.tree_.value
    assert_allclose(orig_tree_values, new_tree_values)