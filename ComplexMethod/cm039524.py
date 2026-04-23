def test_precision_recall_display_name(pyplot, constructor_name, default_label):
    """Check the behaviour of the name parameters"""
    X, y = make_classification(n_classes=2, n_samples=100, random_state=0)
    pos_label = 1

    classifier = LogisticRegression()
    n_cv = 3
    cv_results = cross_validate(
        classifier, X, y, cv=n_cv, return_estimator=True, return_indices=True
    )
    classifier.fit(X, y)
    y_score = classifier.predict_proba(X)[:, pos_label]

    if constructor_name == "from_estimator":
        display = PrecisionRecallDisplay.from_estimator(classifier, X, y)
    elif constructor_name == "from_predictions":
        display = PrecisionRecallDisplay.from_predictions(
            y, y_score, pos_label=pos_label
        )
    else:  # constructor_name = "from_cv_results"
        display = PrecisionRecallDisplay.from_cv_results(cv_results, X, y)

    if constructor_name == "from_cv_results":
        average_precision = []
        for idx in range(n_cv):
            test_indices = cv_results["indices"]["test"][idx]
            y_score, _ = _get_response_values_binary(
                cv_results["estimator"][idx],
                _safe_indexing(X, test_indices),
                response_method="auto",
            )
            average_precision.append(
                average_precision_score(
                    _safe_indexing(y, test_indices), y_score, pos_label=pos_label
                )
            )
        # By default, only the first curve is labelled
        assert display.line_[0].get_label() == default_label.format(
            np.mean(average_precision), np.std(average_precision)
        )

        # check that the name can be set
        display.plot(name="MySpecialEstimator")
        # Sets only first labelled curve
        assert display.line_[0].get_label() == (
            f"MySpecialEstimator (AP = {np.mean(average_precision):.2f} +/- "
            f"{np.std(average_precision):.2f})"
        )
    else:
        average_precision = average_precision_score(y, y_score, pos_label=pos_label)

        # check that the default name is used
        assert display.line_.get_label() == default_label.format(average_precision)

        # check that the name can be set
        display.plot(name="MySpecialEstimator")
        assert (
            display.line_.get_label()
            == f"MySpecialEstimator (AP = {average_precision:.2f})"
        )