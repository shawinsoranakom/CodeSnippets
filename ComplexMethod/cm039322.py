def test_calibration_display_name_multiple_calls(
    constructor_name, pyplot, iris_data_binary
):
    # Check that the `name` used when calling
    # `CalibrationDisplay.from_predictions` or
    # `CalibrationDisplay.from_estimator` is used when multiple
    # `CalibrationDisplay.viz.plot()` calls are made.
    X, y = iris_data_binary
    clf_name = "my hand-crafted name"
    clf = LogisticRegression().fit(X, y)
    y_prob = clf.predict_proba(X)[:, 1]

    constructor = getattr(CalibrationDisplay, constructor_name)
    params = (clf, X, y) if constructor_name == "from_estimator" else (y, y_prob)

    viz = constructor(*params, name=clf_name)
    assert viz.estimator_name == clf_name
    pyplot.close("all")
    viz.plot()

    expected_legend_labels = [clf_name, "Perfectly calibrated"]
    legend_labels = viz.ax_.get_legend().get_texts()
    assert len(legend_labels) == len(expected_legend_labels)
    for labels in legend_labels:
        assert labels.get_text() in expected_legend_labels

    pyplot.close("all")
    clf_name = "another_name"
    viz.plot(name=clf_name)
    assert len(legend_labels) == len(expected_legend_labels)
    for labels in legend_labels:
        assert labels.get_text() in expected_legend_labels