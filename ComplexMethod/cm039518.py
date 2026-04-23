def test_plot_roc_curve_despine(pyplot, data_binary, despine, constructor_name):
    # Check that the despine keyword is working correctly
    X, y = data_binary

    lr = LogisticRegression().fit(X, y)
    lr.fit(X, y)
    cv_results = cross_validate(
        LogisticRegression(), X, y, cv=3, return_estimator=True, return_indices=True
    )

    y_pred = lr.decision_function(X)

    # safe guard for the if/else construction
    assert constructor_name in ("from_estimator", "from_predictions", "from_cv_results")

    if constructor_name == "from_estimator":
        display = RocCurveDisplay.from_estimator(lr, X, y, despine=despine)
    elif constructor_name == "from_predictions":
        display = RocCurveDisplay.from_predictions(y, y_pred, despine=despine)
    else:
        display = RocCurveDisplay.from_cv_results(cv_results, X, y, despine=despine)

    for s in ["top", "right"]:
        assert display.ax_.spines[s].get_visible() is not despine

    if despine:
        for s in ["bottom", "left"]:
            assert display.ax_.spines[s].get_bounds() == (0, 1)