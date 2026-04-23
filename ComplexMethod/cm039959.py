def test_validate_curve_kwargs_single_legend(
    name, legend_metric, legend_metric_name, curve_kwargs
):
    """Check `_validate_curve_kwargs` returns correct kwargs for single legend entry."""
    n_curves = 3
    curve_kwargs_out = _BinaryClassifierCurveDisplayMixin._validate_curve_kwargs(
        n_curves=n_curves,
        name=name,
        legend_metric=legend_metric,
        legend_metric_name=legend_metric_name,
        curve_kwargs=curve_kwargs,
    )

    assert isinstance(curve_kwargs_out, list)
    assert len(curve_kwargs_out) == n_curves

    expected_label = None
    if isinstance(name, list):
        name = name[0]
    if name is not None:
        expected_label = name
        if legend_metric["mean"] is not None:
            expected_label = expected_label + f" ({legend_metric_name} = 0.80 +/- 0.20)"
    # `name` is None
    elif legend_metric["mean"] is not None:
        expected_label = f"{legend_metric_name} = 0.80 +/- 0.20"

    assert curve_kwargs_out[0]["label"] == expected_label
    # All remaining curves should have None as "label"
    assert curve_kwargs_out[1]["label"] is None
    assert curve_kwargs_out[2]["label"] is None

    if curve_kwargs is None:
        assert all("color" not in kwargs for kwargs in curve_kwargs_out)
    else:
        assert all(kwargs["color"] == "red" for kwargs in curve_kwargs_out)