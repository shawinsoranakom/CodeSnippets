def test_display_from_cv_results_legend_label(
    pyplot, Display, auc_metrics, auc_metric_name, curve_kwargs, name
):
    """Check legend label correct with all `curve_kwargs`, `name` combinations.

    This function verifies that the legend labels in a Display object created from
    cross-validation results are correctly formatted based on the provided parameters.
    """
    X, y = X, y = make_classification(n_classes=2, n_samples=50, random_state=0)
    cv_results = cross_validate(
        LogisticRegression(), X, y, cv=3, return_estimator=True, return_indices=True
    )

    if not isinstance(curve_kwargs, list) and isinstance(name, list):
        with pytest.raises(ValueError, match="To avoid labeling individual curves"):
            Display.from_cv_results(
                cv_results, X, y, name=name, curve_kwargs=curve_kwargs
            )
    else:
        display = Display.from_cv_results(
            cv_results, X, y, name=name, curve_kwargs=curve_kwargs
        )

        legend = display.ax_.get_legend()
        legend_labels = [text.get_text() for text in legend.get_texts()]
        if isinstance(curve_kwargs, list):
            # Multiple labels in legend
            assert len(legend_labels) == 3
            for idx, label in enumerate(legend_labels):
                if name is None:
                    assert label == f"{auc_metric_name} = {auc_metrics[idx]:.2f}"
                elif isinstance(name, str):
                    assert (
                        label == f"single ({auc_metric_name} = {auc_metrics[idx]:.2f})"
                    )
                else:
                    # `name` is a list of different strings
                    assert (
                        label
                        == f"{name[idx]} ({auc_metric_name} = {auc_metrics[idx]:.2f})"
                    )
        else:
            # Single label in legend
            assert len(legend_labels) == 1
            if name is None:
                assert legend_labels[0] == (
                    f"{auc_metric_name} = {np.mean(auc_metrics):.2f} +/- "
                    f"{np.std(auc_metrics):.2f}"
                )
            else:
                # name is single string
                assert legend_labels[0] == (
                    f"single ({auc_metric_name} = {np.mean(auc_metrics):.2f} +/- "
                    f"{np.std(auc_metrics):.2f})"
                )
    # Close plots, prevents "more than 20 figures" opened warning
    pyplot.close("all")