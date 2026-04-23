def test_validate_curve_kwargs_multi_legend(name, legend_metric, legend_metric_name):
    """Check `_validate_curve_kwargs` returns correct kwargs for multi legend entry."""
    n_curves = 3
    curve_kwargs = [{"color": "red"}, {"color": "yellow"}, {"color": "blue"}]
    curve_kwargs_out = _BinaryClassifierCurveDisplayMixin._validate_curve_kwargs(
        n_curves=n_curves,
        name=name,
        legend_metric=legend_metric,
        legend_metric_name=legend_metric_name,
        curve_kwargs=curve_kwargs,
    )

    assert isinstance(curve_kwargs_out, list)
    assert len(curve_kwargs_out) == n_curves

    expected_labels = [None, None, None]
    if isinstance(name, str):
        expected_labels = "curve_name"
        if legend_metric["metric"][0] is not None:
            expected_labels = expected_labels + f" ({legend_metric_name} = 1.00)"
        expected_labels = [expected_labels] * n_curves
    elif isinstance(name, list) and legend_metric["metric"][0] is None:
        expected_labels = name
    elif isinstance(name, list) and legend_metric["metric"][0] is not None:
        expected_labels = [
            f"{name_single} ({legend_metric_name} = 1.00)" for name_single in name
        ]
    # `name` is None
    elif legend_metric["metric"][0] is not None:
        expected_labels = [f"{legend_metric_name} = 1.00"] * n_curves

    for idx, expected_label in enumerate(expected_labels):
        assert curve_kwargs_out[idx]["label"] == expected_label

    for curve_kwarg, curve_kwarg_out in zip(curve_kwargs, curve_kwargs_out):
        assert curve_kwarg_out["color"] == curve_kwarg["color"]