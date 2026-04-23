def test_grid_search_pipeline_steps():
    # check that parameters that are estimators are cloned before fitting
    pipe = Pipeline([("regressor", LinearRegression())])
    param_grid = {"regressor": [LinearRegression(), Ridge()]}
    grid_search = GridSearchCV(pipe, param_grid, cv=2)
    grid_search.fit(X, y)
    regressor_results = grid_search.cv_results_["param_regressor"]
    assert isinstance(regressor_results[0], LinearRegression)
    assert isinstance(regressor_results[1], Ridge)
    assert not hasattr(regressor_results[0], "coef_")
    assert not hasattr(regressor_results[1], "coef_")
    assert regressor_results[0] is not grid_search.best_estimator_
    assert regressor_results[1] is not grid_search.best_estimator_
    # check that we didn't modify the parameter grid that was passed
    assert not hasattr(param_grid["regressor"][0], "coef_")
    assert not hasattr(param_grid["regressor"][1], "coef_")