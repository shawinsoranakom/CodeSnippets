def test_plot_precision_recall_despine(pyplot, despine, constructor_name):
    # Check that the despine keyword is working correctly
    X, y = make_classification(n_classes=2, n_samples=50, random_state=0)

    clf = LogisticRegression().fit(X, y)
    clf.fit(X, y)
    cv_results = cross_validate(
        LogisticRegression(), X, y, cv=3, return_estimator=True, return_indices=True
    )

    y_score = clf.decision_function(X)

    if constructor_name == "from_estimator":
        display = PrecisionRecallDisplay.from_estimator(clf, X, y, despine=despine)
    elif constructor_name == "from_predictions":
        display = PrecisionRecallDisplay.from_predictions(y, y_score, despine=despine)
    else:
        display = PrecisionRecallDisplay.from_cv_results(
            cv_results, X, y, despine=despine
        )

    for s in ["top", "right"]:
        assert display.ax_.spines[s].get_visible() is not despine

    if despine:
        for s in ["bottom", "left"]:
            assert display.ax_.spines[s].get_bounds() == (0, 1)