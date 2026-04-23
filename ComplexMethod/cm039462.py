def test_draw_indices_using_sample_weight(
    bagging_class, accept_sample_weight, metadata_routing, max_samples
):
    X = np.arange(100).reshape(-1, 1)
    y = np.repeat([0, 1], 50)
    # all indices except 4 and 5 have zero weight
    sample_weight = np.zeros(100)
    sample_weight[4] = 1
    sample_weight[5] = 2
    if accept_sample_weight:
        base_estimator = EstimatorAcceptingSampleWeight()
    else:
        base_estimator = EstimatorRejectingSampleWeight()

    n_samples, n_features = X.shape

    if isinstance(max_samples, float):
        # max_samples passed as a fraction of the input data. Since
        # sample_weight are provided, the effective number of samples is the
        # sum of the sample weights.
        expected_integer_max_samples = int(max_samples * sample_weight.sum())
    else:
        expected_integer_max_samples = max_samples

    with config_context(enable_metadata_routing=metadata_routing):
        # TODO(slep006): remove block when default routing is implemented
        if metadata_routing and accept_sample_weight:
            base_estimator = base_estimator.set_fit_request(sample_weight=True)
        bagging = bagging_class(base_estimator, max_samples=max_samples, n_estimators=4)
        bagging.fit(X, y, sample_weight=sample_weight)
        for estimator, samples in zip(bagging.estimators_, bagging.estimators_samples_):
            counts = np.bincount(samples, minlength=n_samples)
            assert sum(counts) == len(samples) == expected_integer_max_samples
            # only indices 4 and 5 should appear
            assert np.isin(samples, [4, 5]).all()
            if accept_sample_weight:
                # sampled indices represented through weighting
                assert estimator.X_.shape == (n_samples, n_features)
                assert estimator.y_.shape == (n_samples,)
                assert_allclose(estimator.X_, X)
                assert_allclose(estimator.y_, y)
                assert_allclose(estimator.sample_weight_, counts)
            else:
                # sampled indices represented through indexing
                assert estimator.X_.shape == (expected_integer_max_samples, n_features)
                assert estimator.y_.shape == (expected_integer_max_samples,)
                assert_allclose(estimator.X_, X[samples])
                assert_allclose(estimator.y_, y[samples])