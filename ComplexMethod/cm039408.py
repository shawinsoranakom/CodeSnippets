def test_neigh_predictions_algorithm_agnosticity(
    global_dtype,
    n_samples,
    n_features,
    n_query_pts,
    metric,
    n_neighbors,
    radius,
    NeighborsMixinSubclass,
):
    # The different algorithms must return identical predictions results
    # on their common metrics.

    metric = _parse_metric(metric, global_dtype)
    if isinstance(metric, DistanceMetric):
        if "Classifier" in NeighborsMixinSubclass.__name__:
            pytest.skip(
                "Metrics of type `DistanceMetric` are not yet supported for"
                " classifiers."
            )
        if "Radius" in NeighborsMixinSubclass.__name__:
            pytest.skip(
                "Metrics of type `DistanceMetric` are not yet supported for"
                " radius-neighbor estimators."
            )

    # Redefining the rng locally to use the same generated X
    local_rng = np.random.RandomState(0)
    X = local_rng.rand(n_samples, n_features).astype(global_dtype, copy=False)
    y = local_rng.randint(3, size=n_samples)

    query = local_rng.rand(n_query_pts, n_features).astype(global_dtype, copy=False)

    predict_results = []

    parameter = (
        n_neighbors if issubclass(NeighborsMixinSubclass, KNeighborsMixin) else radius
    )

    for algorithm in ALGORITHMS:
        if isinstance(metric, DistanceMetric) and global_dtype == np.float32:
            if "tree" in algorithm:  # pragma: nocover
                pytest.skip(
                    "Neither KDTree nor BallTree support 32-bit distance metric"
                    " objects."
                )
        neigh = NeighborsMixinSubclass(parameter, algorithm=algorithm, metric=metric)
        neigh.fit(X, y)

        predict_results.append(neigh.predict(query))

    for i in range(len(predict_results) - 1):
        algorithm = ALGORITHMS[i]
        next_algorithm = ALGORITHMS[i + 1]

        predictions, next_predictions = predict_results[i], predict_results[i + 1]

        assert_allclose(
            predictions,
            next_predictions,
            err_msg=(
                f"The '{algorithm}' and '{next_algorithm}' "
                "algorithms return different predictions."
            ),
        )