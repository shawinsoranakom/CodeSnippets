def test_output_shape(
    Estimator, method, data, grid_resolution, features, kind, use_custom_values
):
    # Check that partial_dependence has consistent output shape for different
    # kinds of estimators:
    # - classifiers with binary and multiclass settings
    # - regressors
    # - multi-task regressors

    est = Estimator()
    if hasattr(est, "n_estimators"):
        est.set_params(n_estimators=2)  # speed-up computations

    # n_target corresponds to the number of classes (1 for binary classif) or
    # the number of tasks / outputs in multi task settings. It's equal to 1 for
    # classical regression_data.
    (X, y), n_targets = data
    n_instances = X.shape[0]

    custom_values = None
    if use_custom_values:
        grid_resolution = 5
        custom_values = {f: X[:grid_resolution, f] for f in features}

    est.fit(X, y)
    result = partial_dependence(
        est,
        X=X,
        features=features,
        method=method,
        kind=kind,
        grid_resolution=grid_resolution,
        custom_values=custom_values,
    )
    pdp, axes = result, result["grid_values"]

    expected_pdp_shape = (n_targets, *[grid_resolution for _ in range(len(features))])
    expected_ice_shape = (
        n_targets,
        n_instances,
        *[grid_resolution for _ in range(len(features))],
    )
    if kind == "average":
        assert pdp.average.shape == expected_pdp_shape
    elif kind == "individual":
        assert pdp.individual.shape == expected_ice_shape
    else:  # 'both'
        assert pdp.average.shape == expected_pdp_shape
        assert pdp.individual.shape == expected_ice_shape

    expected_axes_shape = (len(features), grid_resolution)
    assert axes is not None
    assert np.asarray(axes).shape == expected_axes_shape