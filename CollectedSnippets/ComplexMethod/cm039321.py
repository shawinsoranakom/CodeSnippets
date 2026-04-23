def test_calibration_display_compute(pyplot, iris_data_binary, n_bins, strategy):
    # Ensure `CalibrationDisplay.from_predictions` and `calibration_curve`
    # compute the same results. Also checks attributes of the
    # CalibrationDisplay object.
    X, y = iris_data_binary

    lr = LogisticRegression().fit(X, y)

    viz = CalibrationDisplay.from_estimator(
        lr, X, y, n_bins=n_bins, strategy=strategy, alpha=0.8
    )

    y_prob = lr.predict_proba(X)[:, 1]
    prob_true, prob_pred = calibration_curve(
        y, y_prob, n_bins=n_bins, strategy=strategy
    )

    assert_allclose(viz.prob_true, prob_true)
    assert_allclose(viz.prob_pred, prob_pred)
    assert_allclose(viz.y_prob, y_prob)

    assert viz.estimator_name == "LogisticRegression"

    # cannot fail thanks to pyplot fixture
    import matplotlib as mpl

    assert isinstance(viz.line_, mpl.lines.Line2D)
    assert viz.line_.get_alpha() == 0.8
    assert isinstance(viz.ax_, mpl.axes.Axes)
    assert isinstance(viz.figure_, mpl.figure.Figure)

    assert viz.ax_.get_xlabel() == "Mean predicted probability (Positive class: 1)"
    assert viz.ax_.get_ylabel() == "Fraction of positives (Positive class: 1)"

    expected_legend_labels = ["LogisticRegression", "Perfectly calibrated"]
    legend_labels = viz.ax_.get_legend().get_texts()
    assert len(legend_labels) == len(expected_legend_labels)
    for labels in legend_labels:
        assert labels.get_text() in expected_legend_labels