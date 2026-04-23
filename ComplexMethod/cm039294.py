def test_gnb_array_api_compliance(
    use_str_y, use_sample_weight, array_namespace, device_name, dtype_name
):
    """Tests that :class:`GaussianNB` works correctly with array API inputs."""
    xp, device = _array_api_for_tests(array_namespace, device_name)
    X_np = X.astype(dtype_name)
    X_xp = xp.asarray(X_np, device=device)
    if use_str_y:
        y_np = np.array(["a", "a", "a", "b", "b", "b"])
        y_xp_or_np = np.array(["a", "a", "a", "b", "b", "b"])
    else:
        y_np = y.astype(dtype_name)
        y_xp_or_np = xp.asarray(y_np, device=device)

    if use_sample_weight:
        sample_weight = np.array([1, 2, 3, 1, 2, 3])
    else:
        sample_weight = None

    clf_np = GaussianNB().fit(X_np, y_np, sample_weight=sample_weight)
    y_pred_np = clf_np.predict(X_np)
    y_pred_proba_np = clf_np.predict_proba(X_np)
    y_pred_log_proba_np = clf_np.predict_log_proba(X_np)
    with config_context(array_api_dispatch=True):
        clf_xp = GaussianNB().fit(X_xp, y_xp_or_np, sample_weight=sample_weight)
        for fitted_attr in ("class_count_", "class_prior_", "theta_", "var_"):
            xp_attr = getattr(clf_xp, fitted_attr)
            np_attr = getattr(clf_np, fitted_attr)
            assert xp_attr.dtype == X_xp.dtype
            assert array_api_device(xp_attr) == array_api_device(X_xp)
            assert_allclose(move_to(xp_attr, xp=np, device="cpu"), np_attr)

        y_pred_xp = clf_xp.predict(X_xp)
        if not use_str_y:
            assert array_api_device(y_pred_xp) == array_api_device(X_xp)
            y_pred_xp = move_to(y_pred_xp, xp=np, device="cpu")
        assert_array_equal(y_pred_xp, y_pred_np)
        assert y_pred_xp.dtype == y_pred_np.dtype

        y_pred_proba_xp = clf_xp.predict_proba(X_xp)
        assert y_pred_proba_xp.dtype == X_xp.dtype
        assert array_api_device(y_pred_proba_xp) == array_api_device(X_xp)
        assert_allclose(move_to(y_pred_proba_xp, xp=np, device="cpu"), y_pred_proba_np)

        y_pred_log_proba_xp = clf_xp.predict_log_proba(X_xp)
        assert y_pred_log_proba_xp.dtype == X_xp.dtype
        assert array_api_device(y_pred_log_proba_xp) == array_api_device(X_xp)
        assert_allclose(
            move_to(y_pred_log_proba_xp, xp=np, device="cpu"), y_pred_log_proba_np
        )