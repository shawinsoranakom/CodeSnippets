def test_mixed_array_api_namespace_input_compliance(
    metric_name, from_ns_and_device, to_ns_and_device
):
    """Check `y_true` and `sample_weight` follows `y_pred` for mixed namespace inputs.

    Compares the output for all-numpy vs mixed-type inputs.
    If the output is a float, checks that both all-numpy and mixed-type inputs return
    a float.
    If output is an array, checks it is of the same namespace and device as `y_pred`
    (`to_ns_and_device`).
    If the output is a tuple, checks that each element, whether float or array,
    is correct, as detailed above.
    """
    xp_to, device_to = _array_api_for_tests(
        to_ns_and_device.xp, device_name=to_ns_and_device.device
    )
    xp_from, device_from = _array_api_for_tests(
        from_ns_and_device.xp, device_name=from_ns_and_device.device
    )

    metric = ALL_METRICS[metric_name]

    data_all = {
        "binary": ([0, 0, 1, 1], [0, 1, 0, 1]),
        "binary_continuous": ([1, 0, 1, 0], [0.5, 0.2, 0.7, 0.6]),
        "label_indicator_continuous": ([[1, 0, 1, 0]], [[0.5, 0.2, 0.7, 0.6]]),
        "regression_integer": ([2, 1, 3, 4], [2, 1, 2, 2]),
        "regression_continuous": ([2.1, 1.0, 3.0, 4.0], [2.2, 1.1, 2.0, 2.0]),
    }
    sample_weight = [1, 1, 2, 2]

    # Deal with max mps float precision being float32
    def _get_dtype(data, xp, device):
        # Assume list is all float if first element is float
        if isinstance(data[0], float):
            dtype = _max_precision_float_dtype(xp, device)
        else:
            dtype = xp.int64
        return dtype

    if metric_name in CLASSIFICATION_METRICS:
        # These should all accept binary label input as there are no
        # `CLASSIFICATION_METRICS` that are in `METRIC_UNDEFINED_BINARY` and are
        # NOT `partial`s (which we do not test for in array API compliance)
        data_cases = ["binary"]
    elif metric_name in {**CONTINUOUS_CLASSIFICATION_METRICS, **CURVE_METRICS}:
        if metric_name not in METRIC_UNDEFINED_BINARY:
            data_cases = ["binary_continuous"]
        else:
            data_cases = ["label_indicator_continuous"]
    elif metric_name in REGRESSION_METRICS:
        data_cases = ["regression_integer", "regression_continuous"]

    with config_context(array_api_dispatch=True):
        for data_case in data_cases:
            y1, y2 = data_all[data_case]

            dtype = _get_dtype(y1, xp_from, device_from)
            y1_xp = xp_from.asarray(y1, device=device_from, dtype=dtype)

            metric_kwargs_xp = metric_kwargs_np = {}
            if metric_name not in METRICS_WITHOUT_SAMPLE_WEIGHT:
                # use `from_ns_and_device` for `sample_weight` as well
                sample_weight_np = np.array(sample_weight)
                metric_kwargs_np = {"sample_weight": sample_weight_np}
                sample_weight_xp = xp_from.asarray(sample_weight_np, device=device_from)
                metric_kwargs_xp = {"sample_weight": sample_weight_xp}

            dtype = _get_dtype(y2, xp_to, device_to)
            y2_xp = xp_to.asarray(y2, device=device_to, dtype=dtype)

            metric_xp = metric(y1_xp, y2_xp, **metric_kwargs_xp)
            metric_np = metric(y1, y2, **metric_kwargs_np)

            if isinstance(metric_np, Tuple):
                for out_np, out_xp in zip(metric_np, metric_xp):
                    _check_output(out_np, out_xp, xp_to, y2_xp)
            else:
                _check_output(metric_np, metric_xp, xp_to, y2_xp)