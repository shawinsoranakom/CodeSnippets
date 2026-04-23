def test_stacking_regressor_diabetes(cv, final_estimator, predict_params, passthrough):
    # prescale the data to avoid convergence warning without using a pipeline
    # for later assert
    X_train, X_test, y_train, _ = train_test_split(
        scale(X_diabetes), y_diabetes, random_state=42
    )
    estimators = [("lr", LinearRegression()), ("svr", LinearSVR())]
    reg = StackingRegressor(
        estimators=estimators,
        final_estimator=final_estimator,
        cv=cv,
        passthrough=passthrough,
    )
    reg.fit(X_train, y_train)
    result = reg.predict(X_test, **predict_params)
    expected_result_length = 2 if predict_params else 1
    if predict_params:
        assert len(result) == expected_result_length

    X_trans = reg.transform(X_test)
    expected_column_count = 12 if passthrough else 2
    assert X_trans.shape[1] == expected_column_count
    if passthrough:
        assert_allclose(X_test, X_trans[:, -10:])

    reg.set_params(lr="drop")
    reg.fit(X_train, y_train)
    reg.predict(X_test)

    X_trans = reg.transform(X_test)
    expected_column_count_drop = 11 if passthrough else 1
    assert X_trans.shape[1] == expected_column_count_drop
    if passthrough:
        assert_allclose(X_test, X_trans[:, -10:])