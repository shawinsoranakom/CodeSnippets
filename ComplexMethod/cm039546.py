def test_pairwise_parallel_array_api(
    func, metric, kwds, array_namespace, device_name, dtype_name
):
    xp, device = _array_api_for_tests(array_namespace, device_name)
    rng = np.random.RandomState(0)
    X_np = np.array(5 * rng.random_sample((5, 4)), dtype=dtype_name)
    Y_np = np.array(5 * rng.random_sample((3, 4)), dtype=dtype_name)
    X_xp = xp.asarray(X_np, device=device)
    Y_xp = xp.asarray(Y_np, device=device)

    with config_context(array_api_dispatch=True):
        for y_val in (None, "not none"):
            Y_xp = None if y_val is None else Y_xp
            Y_np = None if y_val is None else Y_np

            n_job1_xp = func(X_xp, Y_xp, metric=metric, n_jobs=1, **kwds)
            n_job1_xp_np = move_to(n_job1_xp, xp=np, device="cpu")
            assert get_namespace(n_job1_xp)[0].__name__ == xp.__name__
            assert n_job1_xp.device == X_xp.device
            assert n_job1_xp.dtype == X_xp.dtype

            n_job2_xp = func(X_xp, Y_xp, metric=metric, n_jobs=2, **kwds)
            n_job2_xp_np = move_to(n_job2_xp, xp=np, device="cpu")
            assert get_namespace(n_job2_xp)[0].__name__ == xp.__name__
            assert n_job2_xp.device == X_xp.device
            assert n_job2_xp.dtype == X_xp.dtype

            n_job2_np = func(X_np, metric=metric, n_jobs=2, **kwds)

            assert_allclose(n_job1_xp_np, n_job2_xp_np)
            assert_allclose(n_job2_xp_np, n_job2_np)