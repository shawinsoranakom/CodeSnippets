def test_forest_classifier_oob(
    ForestClassifier, X, y, X_type, lower_bound_accuracy, oob_score
):
    """Check that OOB score is close to score on a test set."""
    X = _convert_container(X, constructor_name=X_type)
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.5,
        random_state=0,
    )
    classifier = ForestClassifier(
        n_estimators=40,
        bootstrap=True,
        oob_score=oob_score,
        random_state=0,
    )

    assert not hasattr(classifier, "oob_score_")
    assert not hasattr(classifier, "oob_decision_function_")

    classifier.fit(X_train, y_train)
    if callable(oob_score):
        test_score = oob_score(y_test, classifier.predict(X_test))
    else:
        test_score = classifier.score(X_test, y_test)
        assert classifier.oob_score_ >= lower_bound_accuracy

    abs_diff = abs(test_score - classifier.oob_score_)
    assert abs_diff <= 0.11, f"{abs_diff=} is greater than 0.11"

    assert hasattr(classifier, "oob_score_")
    assert not hasattr(classifier, "oob_prediction_")
    assert hasattr(classifier, "oob_decision_function_")

    if y.ndim == 1:
        expected_shape = (X_train.shape[0], len(set(y)))
    else:
        expected_shape = (X_train.shape[0], len(set(y[:, 0])), y.shape[1])
    assert classifier.oob_decision_function_.shape == expected_shape