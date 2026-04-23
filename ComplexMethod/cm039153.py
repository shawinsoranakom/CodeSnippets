def test_pca_mle_array_api_compliance(
    estimator, check, array_namespace, device_name, dtype_name
):
    name = estimator.__class__.__name__
    check(
        name,
        estimator,
        array_namespace,
        device_name=device_name,
        dtype_name=dtype_name,
    )

    # Simpler variant of the generic check_array_api_input checker tailored for
    # the specific case of PCA with mle-trimmed components.
    xp, device = _array_api_for_tests(array_namespace, device_name)

    X, y = make_classification(random_state=42)
    X = X.astype(dtype_name, copy=False)
    atol = _atol_for_type(X.dtype)

    est = clone(estimator)

    X_xp = xp.asarray(X, device=device)
    y_xp = xp.asarray(y, device=device)

    est.fit(X, y)

    components_np = est.components_
    explained_variance_np = est.explained_variance_

    est_xp = clone(est)
    with config_context(array_api_dispatch=True):
        est_xp.fit(X_xp, y_xp)
        components_xp = est_xp.components_
        assert array_device(components_xp) == array_device(X_xp)
        components_xp_np = move_to(components_xp, xp=np, device="cpu")

        explained_variance_xp = est_xp.explained_variance_
        assert array_device(explained_variance_xp) == array_device(X_xp)
        explained_variance_xp_np = move_to(explained_variance_xp, xp=np, device="cpu")

    assert components_xp_np.dtype == components_np.dtype
    assert components_xp_np.shape[1] == components_np.shape[1]
    assert explained_variance_xp_np.dtype == explained_variance_np.dtype

    # Check that the explained variance values match for the
    # common components:
    min_components = min(components_xp_np.shape[0], components_np.shape[0])
    assert_allclose(
        explained_variance_xp_np[:min_components],
        explained_variance_np[:min_components],
        atol=atol,
    )

    # If the number of components differ, check that the explained variance of
    # the trimmed components is very small.
    if components_xp_np.shape[0] != components_np.shape[0]:
        reference_variance = explained_variance_np[-1]
        extra_variance_np = explained_variance_np[min_components:]
        extra_variance_xp_np = explained_variance_xp_np[min_components:]
        assert all(np.abs(extra_variance_np - reference_variance) < atol)
        assert all(np.abs(extra_variance_xp_np - reference_variance) < atol)