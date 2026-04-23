def test_forest_regressor_oob(ForestRegressor, X, y, X_type, lower_bound_r2, oob_score):
    """Check that forest-based regressor provide an OOB score close to the
    score on a test set."""
    X = _convert_container(X, constructor_name=X_type)
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.5,
        random_state=0,
    )
    regressor = ForestRegressor(
        n_estimators=50,
        bootstrap=True,
        oob_score=oob_score,
        random_state=0,
    )

    assert not hasattr(regressor, "oob_score_")
    assert not hasattr(regressor, "oob_prediction_")

    regressor.fit(X_train, y_train)
    if callable(oob_score):
        test_score = oob_score(y_test, regressor.predict(X_test))
    else:
        test_score = regressor.score(X_test, y_test)
        assert regressor.oob_score_ >= lower_bound_r2

    assert abs(test_score - regressor.oob_score_) <= 0.1

    assert hasattr(regressor, "oob_score_")
    assert hasattr(regressor, "oob_prediction_")
    assert not hasattr(regressor, "oob_decision_function_")

    if y.ndim == 1:
        expected_shape = (X_train.shape[0],)
    else:
        expected_shape = (X_train.shape[0], y.ndim)
    assert regressor.oob_prediction_.shape == expected_shape