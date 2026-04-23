def test_stacking_classifier_iris(cv, final_estimator, passthrough):
    # prescale the data to avoid convergence warning without using a pipeline
    # for later assert
    X_train, X_test, y_train, y_test = train_test_split(
        scale(X_iris), y_iris, stratify=y_iris, random_state=42
    )
    estimators = [("lr", LogisticRegression()), ("svc", LinearSVC())]
    clf = StackingClassifier(
        estimators=estimators,
        final_estimator=final_estimator,
        cv=cv,
        passthrough=passthrough,
    )
    clf.fit(X_train, y_train)
    clf.predict(X_test)
    clf.predict_proba(X_test)
    assert clf.score(X_test, y_test) > 0.8

    X_trans = clf.transform(X_test)
    expected_column_count = 10 if passthrough else 6
    assert X_trans.shape[1] == expected_column_count
    if passthrough:
        assert_allclose(X_test, X_trans[:, -4:])

    clf.set_params(lr="drop")
    clf.fit(X_train, y_train)
    clf.predict(X_test)
    clf.predict_proba(X_test)
    if final_estimator is None:
        # LogisticRegression has decision_function method
        clf.decision_function(X_test)

    X_trans = clf.transform(X_test)
    expected_column_count_drop = 7 if passthrough else 3
    assert X_trans.shape[1] == expected_column_count_drop
    if passthrough:
        assert_allclose(X_test, X_trans[:, -4:])