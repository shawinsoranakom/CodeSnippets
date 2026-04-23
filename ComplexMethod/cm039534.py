def test_display_plot_legend_label(
    pyplot, Display, auc_metric_name, auc_arg_name, display_args, curve_kwargs, name
):
    """Check legend label correct with all `curve_kwargs`, `name` combinations.

    Checks `from_estimator` and `from_predictions` methods, when plotting multiple
    curves.
    """
    if not isinstance(curve_kwargs, list) and isinstance(name, list):
        with pytest.raises(ValueError, match="To avoid labeling individual curves"):
            Display(**display_args).plot(name=name, curve_kwargs=curve_kwargs)
        return

    display = Display(**display_args).plot(name=name, curve_kwargs=curve_kwargs)
    legend = display.ax_.get_legend()
    auc_metric = display_args[auc_arg_name]

    if legend is None:
        # No legend is created, exit test early
        assert name is None
        assert auc_metric is None
        return
    else:
        legend_labels = [text.get_text() for text in legend.get_texts()]

    if isinstance(curve_kwargs, list):
        # Multiple labels in legend
        assert len(legend_labels) == 3
        for idx, label in enumerate(legend_labels):
            if name is None:
                expected_label = f"{auc_metric_name} = 1.00" if auc_metric else None
                assert label == expected_label
            elif isinstance(name, str):
                expected_label = (
                    f"single ({auc_metric_name} = 1.00)" if auc_metric else "single"
                )
                assert label == expected_label
            else:
                # `name` is a list of different strings
                expected_label = (
                    f"{name[idx]} ({auc_metric_name} = 1.00)"
                    if auc_metric
                    else f"{name[idx]}"
                )
                assert label == expected_label
    else:
        # Single label in legend
        assert len(legend_labels) == 1
        if name is None:
            expected_label = (
                f"{auc_metric_name} = 1.00 +/- 0.00" if auc_metric else None
            )
            assert legend_labels[0] == expected_label
        else:
            # name is single string
            expected_label = (
                f"single ({auc_metric_name} = 1.00 +/- 0.00)"
                if auc_metric
                else "single"
            )
            assert legend_labels[0] == expected_label
    # Close plots, prevents "more than 20 figures" opened warning
    pyplot.close("all")