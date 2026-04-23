def test_neighbors_metrics(
    global_dtype,
    global_random_seed,
    metric,
    n_samples=20,
    n_features=3,
    n_query_pts=2,
    n_neighbors=5,
):
    rng = np.random.RandomState(global_random_seed)

    metric = _parse_metric(metric, global_dtype)

    # Test computing the neighbors for various metrics
    algorithms = ["brute", "ball_tree", "kd_tree"]
    X_train = rng.rand(n_samples, n_features).astype(global_dtype, copy=False)
    X_test = rng.rand(n_query_pts, n_features).astype(global_dtype, copy=False)

    metric_params_list = _generate_test_params_for(metric, n_features)

    for metric_params in metric_params_list:
        # Some metric (e.g. Weighted minkowski) are not supported by KDTree
        exclude_kd_tree = (
            False
            if isinstance(metric, DistanceMetric)
            else metric not in neighbors.VALID_METRICS["kd_tree"]
            or ("minkowski" in metric and "w" in metric_params)
        )
        results = {}
        p = metric_params.pop("p", 2)
        for algorithm in algorithms:
            if isinstance(metric, DistanceMetric) and global_dtype == np.float32:
                if "tree" in algorithm:  # pragma: nocover
                    pytest.skip(
                        "Neither KDTree nor BallTree support 32-bit distance metric"
                        " objects."
                    )
            neigh = neighbors.NearestNeighbors(
                n_neighbors=n_neighbors,
                algorithm=algorithm,
                metric=metric,
                p=p,
                metric_params=metric_params,
            )

            if exclude_kd_tree and algorithm == "kd_tree":
                with pytest.raises(ValueError):
                    neigh.fit(X_train)
                continue

            # Haversine distance only accepts 2D data
            if metric == "haversine":
                feature_sl = slice(None, 2)
                X_train = np.ascontiguousarray(X_train[:, feature_sl])
                X_test = np.ascontiguousarray(X_test[:, feature_sl])

            neigh.fit(X_train)
            results[algorithm] = neigh.kneighbors(X_test, return_distance=True)

        brute_dst, brute_idx = results["brute"]
        ball_tree_dst, ball_tree_idx = results["ball_tree"]

        # The returned distances are always in float64 regardless of the input dtype
        # We need to adjust the tolerance w.r.t the input dtype
        rtol = 1e-7 if global_dtype == np.float64 else 1e-4

        assert_allclose(brute_dst, ball_tree_dst, rtol=rtol)
        assert_array_equal(brute_idx, ball_tree_idx)

        if not exclude_kd_tree:
            kd_tree_dst, kd_tree_idx = results["kd_tree"]
            assert_allclose(brute_dst, kd_tree_dst, rtol=rtol)
            assert_array_equal(brute_idx, kd_tree_idx)

            assert_allclose(ball_tree_dst, kd_tree_dst, rtol=rtol)
            assert_array_equal(ball_tree_idx, kd_tree_idx)