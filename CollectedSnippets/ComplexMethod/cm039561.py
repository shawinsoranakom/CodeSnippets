def check_array_api_metric(
    metric, array_namespace, device_name, dtype_name, a_np, b_np, **metric_kwargs
):
    xp, device = _array_api_for_tests(array_namespace, device_name)

    a_xp = xp.asarray(a_np, device=device)
    b_xp = xp.asarray(b_np, device=device)

    metric_np = metric(a_np, b_np, **metric_kwargs)

    if metric_kwargs.get("sample_weight") is not None:
        metric_kwargs["sample_weight"] = xp.asarray(
            metric_kwargs["sample_weight"], device=device
        )

    multioutput = metric_kwargs.get("multioutput")
    if isinstance(multioutput, np.ndarray):
        metric_kwargs["multioutput"] = xp.asarray(multioutput, device=device)

    # When array API dispatch is disabled, and np.asarray works (for example PyTorch
    # with CPU device), calling the metric function with such numpy compatible inputs
    # should work (albeit by implicitly converting to numpy arrays instead of
    # dispatching to the array library).
    try:
        np.asarray(a_xp)
        np.asarray(b_xp)
        numpy_as_array_works = True
    except (TypeError, RuntimeError, ValueError):
        # PyTorch with CUDA device and CuPy raise TypeError consistently.
        # array-api-strict chose to raise RuntimeError instead. NumPy raises
        # a ValueError if the `__array__` dunder does not return an array.
        # Exception type may need to be updated in the future for other libraries.
        numpy_as_array_works = False

    def _check_metric_matches(metric_a, metric_b, convert_a=False):
        if convert_a:
            metric_a = move_to(xp.asarray(metric_a), xp=np, device="cpu")
        assert_allclose(metric_a, metric_b, atol=_atol_for_type(dtype_name))

    def _check_each_metric_matches(metric_a, metric_b, convert_a=False):
        for metric_a_val, metric_b_val in zip(metric_a, metric_b):
            _check_metric_matches(metric_a_val, metric_b_val, convert_a=convert_a)

    if numpy_as_array_works:
        metric_xp = metric(a_xp, b_xp, **metric_kwargs)

        # Handle cases where multiple return values are not of the same shape,
        # e.g. precision_recall_curve:
        if (
            isinstance(metric_np, tuple)
            and len(set([metric_val.shape for metric_val in metric_np])) > 1
        ):
            _check_each_metric_matches(metric_xp, metric_np)

            metric_xp_mixed_1 = metric(a_np, b_xp, **metric_kwargs)
            _check_each_metric_matches(metric_xp_mixed_1, metric_np)

            metric_xp_mixed_2 = metric(a_xp, b_np, **metric_kwargs)
            _check_each_metric_matches(metric_xp_mixed_2, metric_np)

        else:
            _check_metric_matches(metric_xp, metric_np)

            metric_xp_mixed_1 = metric(a_np, b_xp, **metric_kwargs)
            _check_metric_matches(metric_xp_mixed_1, metric_np)

            metric_xp_mixed_2 = metric(a_xp, b_np, **metric_kwargs)
            _check_metric_matches(metric_xp_mixed_2, metric_np)

    with config_context(array_api_dispatch=True):
        metric_xp = metric(a_xp, b_xp, **metric_kwargs)

        # Handle cases where there are multiple return values, e.g. roc_curve:
        if isinstance(metric_xp, tuple):
            _check_each_metric_matches(metric_xp, metric_np, convert_a=True)
        else:
            _check_metric_matches(metric_xp, metric_np, convert_a=True)