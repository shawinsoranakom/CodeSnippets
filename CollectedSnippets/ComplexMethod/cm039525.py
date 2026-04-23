def test_precision_recall_prevalence_pos_label_reusable(pyplot, constructor_name):
    # Check that even if one passes plot_chance_level=False the first time
    # one can still call disp.plot with plot_chance_level=True and get the
    # chance level line

    import matplotlib as mpl

    X, y = make_classification(n_classes=2, n_samples=50, random_state=0)

    lr = LogisticRegression()
    n_cv = 3
    cv_results = cross_validate(
        lr, X, y, cv=n_cv, return_estimator=True, return_indices=True
    )
    y_score = lr.fit(X, y).predict_proba(X)[:, 1]

    if constructor_name == "from_estimator":
        display = PrecisionRecallDisplay.from_estimator(
            lr, X, y, plot_chance_level=False
        )
    elif constructor_name == "from_predictions":
        display = PrecisionRecallDisplay.from_predictions(
            y, y_score, plot_chance_level=False
        )
    else:
        display = PrecisionRecallDisplay.from_cv_results(
            cv_results, X, y, plot_chance_level=False
        )
    assert display.chance_level_ is None

    # When calling from_estimator or from_predictions,
    # prevalence_pos_label should have been set, so that directly
    # calling plot_chance_level=True should plot the chance level line
    display.plot(plot_chance_level=True)
    if constructor_name == "from_cv_results":
        for idx in range(n_cv):
            assert isinstance(display.chance_level_[idx], mpl.lines.Line2D)
    else:
        assert isinstance(display.chance_level_, mpl.lines.Line2D)