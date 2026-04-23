def test_validate_curve_kwargs_default_kwargs(n_curves, curve_kwargs):
    """Check default kwargs are incorporated correctly."""
    curve_kwargs_out = _BinaryClassifierCurveDisplayMixin._validate_curve_kwargs(
        n_curves=n_curves,
        name="test",
        legend_metric={"mean": 0.8, "std": 0.2},
        legend_metric_name="metric",
        curve_kwargs=curve_kwargs,
        default_curve_kwargs={"color": "blue"},
        default_multi_curve_kwargs={"alpha": 0.7, "linestyle": "--", "color": "green"},
    )
    if n_curves > 1:
        # `default_multi_curve_kwargs` are incorporated
        assert all(kwarg["alpha"] == 0.7 for kwarg in curve_kwargs_out)
        assert all(kwarg["linestyle"] == "--" for kwarg in curve_kwargs_out)
        if curve_kwargs is None:
            # `default_multi_curve_kwargs` over-rides `default_curve_kwargs`
            assert all(kwarg["color"] == "green" for kwarg in curve_kwargs_out)
        else:
            # `curve_kwargs` over-rides any defaults
            assert all(kwarg["color"] == "red" for kwarg in curve_kwargs_out)
    # Single curve
    elif curve_kwargs is None:
        # Use `default_curve_kwargs`
        assert all(kwarg["color"] == "blue" for kwarg in curve_kwargs_out)
    else:
        # Use `curve_kwargs`
        assert all(kwarg["color"] == "red" for kwarg in curve_kwargs_out)