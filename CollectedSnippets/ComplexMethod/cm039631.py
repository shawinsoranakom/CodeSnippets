def test_logistic_regression_array_api_compliance(
    binary,
    use_str_y,
    use_sample_weight,
    class_weight,
    array_namespace,
    device_name,
    dtype_name,
):
    xp, device = _array_api_for_tests(array_namespace, device_name)
    X_np = iris.data.astype(dtype_name, copy=True)
    n_samples, _ = X_np.shape
    X_xp = xp.asarray(X_np, device=device)
    if use_str_y:
        if binary:
            target = (iris.target > 0).astype(np.int64)
            target = np.array(["setosa", "not-setosa"])[target]
            if class_weight == "dict":
                class_weight = {"setosa": 1.0, "not-setosa": 3.0}
        else:
            target = iris.target_names[iris.target]
            if class_weight == "dict":
                class_weight = {"virginica": 1.0, "setosa": 2.0, "versicolor": 3.0}
        y_np = target.copy()
        y_xp_or_np = np.asarray(y_np, copy=True)
    else:
        if binary:
            target = (iris.target > 0).astype(np.int64)
            if class_weight == "dict":
                class_weight = {0: 1.0, 1: 3.0}
        else:
            target = iris.target
            if class_weight == "dict":
                class_weight = {0: 1.0, 1: 2.0, 2: 3.0}
        y_np = target.astype(dtype_name)
        y_xp_or_np = xp.asarray(y_np, device=device)

    if use_sample_weight:
        sample_weight = (
            np.random.default_rng(0)
            .uniform(-1, 5, size=n_samples)
            .clip(0, None)
            .astype(dtype_name)
        )
    else:
        sample_weight = None

    # Use a strong regularization to ensure coef_ can be identified to a higher
    # precision even when taking into account the iterated discrepancies when
    # the gradient is computed in float32. This is only necessary because the
    # iris dataset is perfectly separable.
    # We selected a low value of C (high coef_ regularization) to be able
    # to identify coef_ to some strict enough precision level. However we
    # also want to make sure that this choice of regularization does not
    # constrain the fitted models to a trivial baseline classifier where only
    # the intercept would be non-zero.
    lr_params = dict(
        C=1e-2, solver="lbfgs", tol=1e-12, max_iter=500, class_weight=class_weight
    )
    with warnings.catch_warnings():
        # Make sure that we converge in the reference fit.
        lr_np = LogisticRegression(**lr_params).fit(
            X_np, y_np, sample_weight=sample_weight
        )
        assert lr_np.n_iter_ < lr_np.max_iter

    # Test that C was not too large for meaningful testing.
    assert np.abs(lr_np.coef_).max() > 0.1

    predict_proba_np = lr_np.predict_proba(X_np)
    preditct_log_proba_np = lr_np.predict_log_proba(X_np)
    prediction_np = lr_np.predict(X_np)
    # TODO: those tolerance levels seem quite high. Investigate further if we
    # can hunt down the numerical discrepancies more precisely.
    atol = _atol_for_type(dtype_name) * 10
    rtol = 5e-3 if dtype_name == "float32" else 1e-5

    with config_context(array_api_dispatch=True):
        with warnings.catch_warnings():
            # Make sure that we converge when using the namespace/device
            # specific fit.
            warnings.simplefilter("error", ConvergenceWarning)
            lr_xp = LogisticRegression(**lr_params).fit(
                X_xp, y_xp_or_np, sample_weight=sample_weight
            )

        assert lr_xp.n_iter_.shape == lr_np.n_iter_.shape
        assert int(lr_xp.n_iter_[0]) < lr_xp.max_iter

        for attr_name in ("coef_", "intercept_"):
            attr_xp = getattr(lr_xp, attr_name)
            attr_np = getattr(lr_np, attr_name)
            assert_allclose(
                move_to(attr_xp, xp=np, device="cpu"), attr_np, rtol=rtol, atol=atol
            )
            assert attr_xp.dtype == X_xp.dtype
            assert array_api_device(attr_xp) == array_api_device(X_xp)

        predict_proba_xp = lr_xp.predict_proba(X_xp)
        assert_allclose(
            move_to(predict_proba_xp, xp=np, device="cpu"),
            predict_proba_np,
            rtol=rtol,
            atol=atol,
        )
        assert predict_proba_xp.dtype == X_xp.dtype
        assert array_api_device(predict_proba_xp) == array_api_device(X_xp)

        predict_log_proba_xp = lr_xp.predict_log_proba(X_xp)
        assert_allclose(
            move_to(predict_log_proba_xp, xp=np, device="cpu"),
            preditct_log_proba_np,
            rtol=rtol,
            atol=atol,
        )
        assert predict_log_proba_xp.dtype == X_xp.dtype
        assert array_api_device(predict_log_proba_xp) == array_api_device(X_xp)

        prediction_xp = lr_xp.predict(X_xp)
        if not use_str_y:
            prediction_xp = move_to(prediction_xp, xp=np, device="cpu")
        assert_array_equal(prediction_xp, prediction_np)