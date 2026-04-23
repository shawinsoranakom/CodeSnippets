def check_array_api_input(
    name,
    estimator_orig,
    array_namespace,
    device_name=None,
    dtype_name="float64",
    check_values=False,
    check_sample_weight=False,
    expect_only_array_outputs=True,
):
    """Check that the estimator can work consistently with the Array API

    By default, this just checks that the types and shapes of the arrays are
    consistent with calling the same estimator with numpy arrays.

    When check_values is True, it also checks that calling the estimator on the
    array_api Array gives the same results as ndarrays.

    When check_sample_weight is True, dummy sample weights are passed to the
    fit call.

    When expect_only_array_outputs is False, the check is looser: in particular
    it accepts non-array outputs such as sparse data structures. This is
    useful to test that enabling array API dispatch does not change the
    behavior of any estimator fed with NumPy inputs, even for estimators that
    do not support array API.
    """
    xp, device = _array_api_for_tests(array_namespace, device_name)

    X, y = make_classification(n_samples=30, n_features=10, random_state=42)
    X = X.astype(dtype_name, copy=False)

    X = _enforce_estimator_tags_X(estimator_orig, X)
    y = _enforce_estimator_tags_y(estimator_orig, y)

    est = clone(estimator_orig)
    set_random_state(est)

    X_xp = xp.asarray(X, device=device)
    y_xp = xp.asarray(y, device=device)
    fit_kwargs = {}
    fit_kwargs_xp = {}
    if check_sample_weight:
        fit_kwargs["sample_weight"] = np.ones(X.shape[0], dtype=X.dtype)
        fit_kwargs_xp["sample_weight"] = xp.asarray(
            fit_kwargs["sample_weight"], device=device
        )

    est.fit(X, y, **fit_kwargs)

    array_attributes = {
        key: value for key, value in vars(est).items() if isinstance(value, np.ndarray)
    }

    est_xp = clone(est)
    with config_context(array_api_dispatch=True):
        est_xp.fit(X_xp, y_xp, **fit_kwargs_xp)
        input_ns = get_namespace(X_xp)[0].__name__

    # Fitted attributes which are arrays must have the same
    # namespace as the one of the training data.
    for key, attribute in array_attributes.items():
        est_xp_param = getattr(est_xp, key)
        with config_context(array_api_dispatch=True):
            attribute_ns = get_namespace(est_xp_param)[0].__name__
        assert attribute_ns == input_ns, (
            f"'{key}' attribute is in wrong namespace, expected {input_ns} "
            f"got {attribute_ns}"
        )

        with config_context(array_api_dispatch=True):
            assert array_device(est_xp_param) == array_device(X_xp)

        est_xp_param_np = move_to(est_xp_param, xp=np, device="cpu")
        if check_values:
            assert_allclose(
                attribute,
                est_xp_param_np,
                err_msg=f"{key} not the same",
                atol=_atol_for_type(X.dtype),
            )
        else:
            assert attribute.shape == est_xp_param_np.shape
            if device == "mps" and np.issubdtype(est_xp_param_np.dtype, np.floating):
                # for mps devices the maximum supported floating dtype is float32
                assert est_xp_param_np.dtype == np.float32
            else:
                assert est_xp_param_np.dtype == attribute.dtype

    # Check estimator methods, if supported, give the same results
    methods = (
        "score",
        "score_samples",
        "decision_function",
        "predict",
        "predict_log_proba",
        "predict_proba",
        "transform",
    )

    try:
        np.asarray(X_xp)
        np.asarray(y_xp)
        # TODO There are a few errors in SearchCV with array-api-strict because
        # we end up doing X[train_indices] where X is an array-api-strict array
        # and train_indices is a numpy array. array-api-strict insists
        # train_indices should be an array-api-strict array. On the other hand,
        # all the array API libraries (PyTorch, jax, CuPy) accept indexing with a
        # numpy array. This is probably not worth doing anything about for
        # now since array-api-strict seems a bit too strict ...
        numpy_asarray_works = xp.__name__ != "array_api_strict"

    except (TypeError, RuntimeError, ValueError):
        # PyTorch with CUDA device and CuPy raise TypeError consistently.
        # array-api-strict chose to raise RuntimeError instead. NumPy emits
        # a ValueError if `__array__` dunder does not return an array.
        # Exception type may need to be updated in the future for other libraries.
        numpy_asarray_works = False

    if numpy_asarray_works:
        # In this case, array_api_dispatch is disabled and we rely on np.asarray
        # being called to convert the non-NumPy inputs to NumPy arrays when needed.
        est_fitted_with_as_array = clone(est).fit(X_xp, y_xp)
        # We only do a smoke test for now, in order to avoid complicating the
        # test function even further.
        for method_name in methods:
            method = getattr(est_fitted_with_as_array, method_name, None)
            if method is None:
                continue

            if method_name == "score":
                method(X_xp, y_xp)
            else:
                method(X_xp)

    for method_name in methods:
        method = getattr(est, method_name, None)
        if method is None:
            continue

        if method_name == "score":
            result = method(X, y)
            with config_context(array_api_dispatch=True):
                result_xp = getattr(est_xp, method_name)(X_xp, y_xp)
            # score typically returns a Python float
            assert isinstance(result, float)
            assert isinstance(result_xp, float)
            if check_values:
                assert abs(result - result_xp) < _atol_for_type(X.dtype)
            continue
        else:
            result = method(X)
            with config_context(array_api_dispatch=True):
                result_xp = getattr(est_xp, method_name)(X_xp)

        with config_context(array_api_dispatch=True):
            result_ns = get_namespace(result_xp)[0].__name__
        assert result_ns == input_ns, (
            f"'{method}' output is in wrong namespace, expected {input_ns}, "
            f"got {result_ns}."
        )

        if expect_only_array_outputs:
            with config_context(array_api_dispatch=True):
                assert array_device(result_xp) == array_device(X_xp)

            result_xp_np = move_to(result_xp, xp=np, device="cpu")
            if check_values:
                assert_allclose(
                    result,
                    result_xp_np,
                    err_msg=f"{method} did not the return the same result",
                    atol=_atol_for_type(X.dtype),
                )
            elif hasattr(result, "shape"):
                assert result.shape == result_xp_np.shape
                assert result.dtype == result_xp_np.dtype

        if method_name == "transform" and hasattr(est, "inverse_transform"):
            inverse_result = est.inverse_transform(result)
            with config_context(array_api_dispatch=True):
                inverse_result_xp = est_xp.inverse_transform(result_xp)

            if expect_only_array_outputs:
                with config_context(array_api_dispatch=True):
                    inverse_result_ns = get_namespace(inverse_result_xp)[0].__name__
                assert inverse_result_ns == input_ns, (
                    "'inverse_transform' output is in wrong namespace, expected"
                    f" {input_ns}, got {inverse_result_ns}."
                )
                with config_context(array_api_dispatch=True):
                    assert array_device(result_xp) == array_device(X_xp)

                inverse_result_xp_np = move_to(inverse_result_xp, xp=np, device="cpu")
                if check_values:
                    assert_allclose(
                        inverse_result,
                        inverse_result_xp_np,
                        err_msg="inverse_transform did not the return the same result",
                        atol=_atol_for_type(X.dtype),
                    )
                elif hasattr(result, "shape"):
                    assert inverse_result.shape == inverse_result_xp_np.shape
                    assert inverse_result.dtype == inverse_result_xp_np.dtype