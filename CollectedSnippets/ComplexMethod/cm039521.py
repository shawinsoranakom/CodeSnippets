def test_precision_recall_display_from_cv_results_plotting(
    pyplot, response_method, drop_intermediate, with_sample_weight
):
    """Check the overall plotting of `from_cv_results`."""
    import matplotlib as mpl

    X, y = make_classification(n_classes=2, n_samples=50, random_state=0)
    pos_label = 1

    cv_results = cross_validate(
        LogisticRegression(), X, y, cv=3, return_estimator=True, return_indices=True
    )

    if with_sample_weight:
        rng = np.random.RandomState(42)
        sample_weight = rng.randint(1, 4, size=(X.shape[0]))
    else:
        sample_weight = None

    display = PrecisionRecallDisplay.from_cv_results(
        cv_results,
        X,
        y,
        sample_weight=sample_weight,
        response_method=response_method,
        drop_intermediate=drop_intermediate,
        pos_label=pos_label,
    )

    for idx, (estimator, test_indices) in enumerate(
        zip(cv_results["estimator"], cv_results["indices"]["test"])
    ):
        y_true = _safe_indexing(y, test_indices)
        y_score = getattr(estimator, response_method)(_safe_indexing(X, test_indices))
        y_score = y_score if y_score.ndim == 1 else y_score[:, 1]
        sample_weight_test = (
            _safe_indexing(sample_weight, test_indices)
            if sample_weight is not None
            else None
        )
        precision, recall, _ = precision_recall_curve(
            y_true,
            y_score,
            pos_label=pos_label,
            drop_intermediate=drop_intermediate,
            sample_weight=sample_weight_test,
        )
        average_precision = average_precision_score(
            y_true, y_score, pos_label=pos_label, sample_weight=sample_weight_test
        )

        assert_allclose(display.precision[idx], precision)
        assert_allclose(display.recall[idx], recall)
        assert display.average_precision[idx] == pytest.approx(average_precision)

        assert isinstance(display.line_[idx], mpl.lines.Line2D)
        # Check default curve kwarg
        assert display.line_[idx].get_drawstyle() == "steps-post"

    _check_figure_axes_and_labels(display, pos_label)
    # Check that the chance level line is not plotted by default
    assert display.chance_level_ is None