def test_roc_curve_display_plotting_from_cv_results(
    pyplot,
    data_binary,
    with_strings,
    with_sample_weight,
    response_method,
    drop_intermediate,
    curve_kwargs,
):
    """Check overall plotting of `from_cv_results`."""
    X, y = data_binary

    pos_label = None
    if with_strings:
        y = np.array(["c", "b"])[y]
        pos_label = "c"

    if with_sample_weight:
        rng = np.random.RandomState(42)
        sample_weight = rng.randint(1, 4, size=(X.shape[0]))
    else:
        sample_weight = None

    cv_results = cross_validate(
        LogisticRegression(), X, y, cv=3, return_estimator=True, return_indices=True
    )
    display = RocCurveDisplay.from_cv_results(
        cv_results,
        X,
        y,
        sample_weight=sample_weight,
        drop_intermediate=drop_intermediate,
        response_method=response_method,
        pos_label=pos_label,
        curve_kwargs=curve_kwargs,
    )

    for idx, (estimator, test_indices) in enumerate(
        zip(cv_results["estimator"], cv_results["indices"]["test"])
    ):
        y_true = _safe_indexing(y, test_indices)
        y_pred = _get_response_values_binary(
            estimator,
            _safe_indexing(X, test_indices),
            response_method=response_method,
            pos_label=pos_label,
        )[0]
        sample_weight_fold = (
            None
            if sample_weight is None
            else _safe_indexing(sample_weight, test_indices)
        )
        fpr, tpr, _ = roc_curve(
            y_true,
            y_pred,
            sample_weight=sample_weight_fold,
            drop_intermediate=drop_intermediate,
            pos_label=pos_label,
        )
        assert_allclose(display.roc_auc[idx], auc(fpr, tpr))
        assert_allclose(display.fpr[idx], fpr)
        assert_allclose(display.tpr[idx], tpr)

    assert display.name is None

    import matplotlib as mpl

    _check_figure_axes_and_labels(display, pos_label)
    if with_sample_weight:
        aggregate_expected_labels = ["AUC = 0.64 +/- 0.04", "_child1", "_child2"]
    else:
        aggregate_expected_labels = ["AUC = 0.61 +/- 0.05", "_child1", "_child2"]
    for idx, line in enumerate(display.line_):
        assert isinstance(line, mpl.lines.Line2D)
        # Default alpha for `from_cv_results`
        line.get_alpha() == 0.5
        if isinstance(curve_kwargs, list):
            # Each individual curve labelled
            assert line.get_label() == f"AUC = {display.roc_auc[idx]:.2f}"
        else:
            # Single aggregate label
            assert line.get_label() == aggregate_expected_labels[idx]