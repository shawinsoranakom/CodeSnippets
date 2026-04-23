def test_display_curve_name_overwritten_by_plot_multiple_calls(
    pyplot,
    data_binary,
    Display,
    constructor_name,
):
    """Check passing `name` in `plot` overwrites name passed in `from_*` method."""
    X, y = data_binary
    clf_name = "my hand-crafted name"
    clf = LogisticRegression().fit(X, y)
    y_pred = clf.predict_proba(X)[:, 1]
    cv_results = cross_validate(
        LogisticRegression(), X, y, cv=3, return_estimator=True, return_indices=True
    )

    if constructor_name == "from_estimator":
        disp = Display.from_estimator(clf, X, y, name=clf_name)
    elif constructor_name == "from_predictions":
        disp = Display.from_predictions(y, y_pred, name=clf_name)
    else:  # constructor_name = "from_cv_results"
        if Display in (RocCurveDisplay, PrecisionRecallDisplay):
            disp = Display.from_cv_results(cv_results, X, y, name=clf_name)
        else:
            pytest.skip(f"`from_cv_results` not implemented in {Display}")

    # TODO: Clean-up once `estimator_name` deprecated in all displays
    if Display in (PrecisionRecallDisplay, RocCurveDisplay):
        assert disp.name == clf_name
    else:
        assert disp.estimator_name == clf_name
    pyplot.close("all")
    disp.plot()
    if constructor_name == "from_cv_results":
        assert clf_name in disp.line_[0].get_label()
    else:
        assert clf_name in disp.line_.get_label()
    pyplot.close("all")
    clf_name = "another_name"
    disp.plot(name=clf_name)
    if constructor_name == "from_cv_results":
        assert clf_name in disp.line_[0].get_label()
    else:
        assert clf_name in disp.line_.get_label()