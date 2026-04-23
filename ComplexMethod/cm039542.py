def test_get_scorer_multimetric(pass_estimator):
    """Check that check_scoring is compatible with multi-metric configurations."""
    X, y = make_classification(n_samples=150, n_features=10, random_state=0)
    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)
    clf = LogisticRegression(random_state=0)

    if pass_estimator:
        check_scoring_ = check_scoring
    else:
        check_scoring_ = partial(check_scoring, clf)

    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)

    expected_results = {
        "r2": r2_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_proba[:, 1]),
        "accuracy": accuracy_score(y_test, y_pred),
    }

    for container in [set, list, tuple]:
        scoring = check_scoring_(scoring=container(["r2", "roc_auc", "accuracy"]))
        result = scoring(clf, X_test, y_test)

        assert result.keys() == expected_results.keys()
        for name in result:
            assert result[name] == pytest.approx(expected_results[name])

    def double_accuracy(y_true, y_pred):
        return 2 * accuracy_score(y_true, y_pred)

    custom_scorer = make_scorer(double_accuracy, response_method="predict")

    # dict with different names
    dict_scoring = check_scoring_(
        scoring={
            "my_r2": "r2",
            "my_roc_auc": "roc_auc",
            "double_accuracy": custom_scorer,
        }
    )
    dict_result = dict_scoring(clf, X_test, y_test)
    assert len(dict_result) == 3
    assert dict_result["my_r2"] == pytest.approx(expected_results["r2"])
    assert dict_result["my_roc_auc"] == pytest.approx(expected_results["roc_auc"])
    assert dict_result["double_accuracy"] == pytest.approx(
        2 * expected_results["accuracy"]
    )