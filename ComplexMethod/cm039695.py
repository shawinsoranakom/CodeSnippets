def test_learning_curve():
    n_samples = 30
    n_splits = 3
    X, y = make_classification(
        n_samples=n_samples,
        n_features=1,
        n_informative=1,
        n_redundant=0,
        n_classes=2,
        n_clusters_per_class=1,
        random_state=0,
    )
    estimator = MockImprovingEstimator(n_samples * ((n_splits - 1) / n_splits))
    for shuffle_train in [False, True]:
        with warnings.catch_warnings(record=True) as w:
            (
                train_sizes,
                train_scores,
                test_scores,
                fit_times,
                score_times,
            ) = learning_curve(
                estimator,
                X,
                y,
                cv=KFold(n_splits=n_splits),
                train_sizes=np.linspace(0.1, 1.0, 10),
                shuffle=shuffle_train,
                return_times=True,
            )
        if len(w) > 0:
            raise RuntimeError("Unexpected warning: %r" % w[0].message)
        assert train_scores.shape == (10, 3)
        assert test_scores.shape == (10, 3)
        assert fit_times.shape == (10, 3)
        assert score_times.shape == (10, 3)
        assert_array_equal(train_sizes, np.linspace(2, 20, 10))
        assert_array_almost_equal(train_scores.mean(axis=1), np.linspace(1.9, 1.0, 10))
        assert_array_almost_equal(test_scores.mean(axis=1), np.linspace(0.1, 1.0, 10))

        # Cannot use assert_array_almost_equal for fit and score times because
        # the values are hardware-dependent
        assert fit_times.dtype == "float64"
        assert score_times.dtype == "float64"

        # Test a custom cv splitter that can iterate only once
        with warnings.catch_warnings(record=True) as w:
            train_sizes2, train_scores2, test_scores2 = learning_curve(
                estimator,
                X,
                y,
                cv=OneTimeSplitter(n_splits=n_splits, n_samples=n_samples),
                train_sizes=np.linspace(0.1, 1.0, 10),
                shuffle=shuffle_train,
            )
        if len(w) > 0:
            raise RuntimeError("Unexpected warning: %r" % w[0].message)
        assert_array_almost_equal(train_scores2, train_scores)
        assert_array_almost_equal(test_scores2, test_scores)