def test_gaussian_mixture_array_api_compliance(
    init_params,
    covariance_type,
    array_namespace,
    device_name,
    dtype_name,
    use_gmm_array_constructor_arguments,
):
    """Test that array api works in GaussianMixture.fit()."""
    xp, device = _array_api_for_tests(array_namespace, device_name)

    rng = np.random.RandomState(0)
    rand_data = RandomData(rng)
    X = rand_data.X[covariance_type]
    X = X.astype(dtype_name)

    if use_gmm_array_constructor_arguments:
        additional_kwargs = {
            "means_init": rand_data.means.astype(dtype_name),
            "precisions_init": rand_data.precisions[covariance_type].astype(dtype_name),
            "weights_init": rand_data.weights.astype(dtype_name),
        }
    else:
        additional_kwargs = {}

    gmm = GaussianMixture(
        n_components=rand_data.n_components,
        covariance_type=covariance_type,
        random_state=0,
        init_params=init_params,
        **additional_kwargs,
    )
    gmm.fit(X)

    X_xp = xp.asarray(X, device=device)

    with sklearn.config_context(array_api_dispatch=True):
        gmm_xp = sklearn.clone(gmm)
        for param_name, param_value in additional_kwargs.items():
            arg_xp = xp.asarray(param_value, device=device)
            setattr(gmm_xp, param_name, arg_xp)

        gmm_xp.fit(X_xp)

        assert get_namespace(gmm_xp.means_)[0] == xp
        assert get_namespace(gmm_xp.covariances_)[0] == xp
        assert array_api_device(gmm_xp.means_) == array_api_device(X_xp)
        assert array_api_device(gmm_xp.covariances_) == array_api_device(X_xp)

        predict_xp = gmm_xp.predict(X_xp)
        predict_proba_xp = gmm_xp.predict_proba(X_xp)
        score_samples_xp = gmm_xp.score_samples(X_xp)
        score_xp = gmm_xp.score(X_xp)
        aic_xp = gmm_xp.aic(X_xp)
        bic_xp = gmm_xp.bic(X_xp)
        sample_X_xp, sample_y_xp = gmm_xp.sample(10)

        results = [
            predict_xp,
            predict_proba_xp,
            score_samples_xp,
            sample_X_xp,
            sample_y_xp,
        ]
        for result in results:
            assert get_namespace(result)[0] == xp
            assert array_api_device(result) == array_api_device(X_xp)

        for score in [score_xp, aic_xp, bic_xp]:
            assert isinstance(score, float)

    # Define specific rtol to make tests pass
    default_rtol = 1e-4 if dtype_name == "float32" else 1e-7
    increased_atol = 5e-4 if dtype_name == "float32" else 0
    increased_rtol = 1e-3 if dtype_name == "float32" else 1e-7

    # Check fitted attributes
    assert_allclose(gmm.means_, move_to(gmm_xp.means_, xp=np, device="cpu"))
    assert_allclose(gmm.weights_, move_to(gmm_xp.weights_, xp=np, device="cpu"))
    assert_allclose(
        gmm.covariances_,
        move_to(gmm_xp.covariances_, xp=np, device="cpu"),
        atol=increased_atol,
        rtol=increased_rtol,
    )
    assert_allclose(
        gmm.precisions_cholesky_,
        move_to(gmm_xp.precisions_cholesky_, xp=np, device="cpu"),
        atol=increased_atol,
        rtol=increased_rtol,
    )
    assert_allclose(
        gmm.precisions_,
        move_to(gmm_xp.precisions_, xp=np, device="cpu"),
        atol=increased_atol,
        rtol=increased_rtol,
    )

    # Check methods
    assert (
        adjusted_rand_score(gmm.predict(X), move_to(predict_xp, xp=np, device="cpu"))
        > 0.95
    )
    assert_allclose(
        gmm.predict_proba(X),
        move_to(predict_proba_xp, xp=np, device="cpu"),
        rtol=increased_rtol,
        atol=increased_atol,
    )
    assert_allclose(
        gmm.score_samples(X),
        move_to(score_samples_xp, xp=np, device="cpu"),
        rtol=increased_rtol,
    )
    # comparing Python float so need explicit rtol when X has dtype float32
    assert_allclose(gmm.score(X), score_xp, rtol=default_rtol)
    assert_allclose(gmm.aic(X), aic_xp, rtol=default_rtol)
    assert_allclose(gmm.bic(X), bic_xp, rtol=default_rtol)
    sample_X, sample_y = gmm.sample(10)
    # generated samples are float64 so need explicit rtol when X has dtype float32
    assert_allclose(
        sample_X, move_to(sample_X_xp, xp=np, device="cpu"), rtol=default_rtol
    )
    assert_allclose(sample_y, move_to(sample_y_xp, xp=np, device="cpu"))