def test_early_stopping(MLPEstimator):
    X = X_digits_binary[:100]
    y = y_digits_binary[:100]
    tol = 0.2
    mlp_estimator = MLPEstimator(
        tol=tol, max_iter=3000, solver="sgd", early_stopping=True
    )
    mlp_estimator.fit(X, y)
    assert mlp_estimator.max_iter > mlp_estimator.n_iter_

    assert mlp_estimator.best_loss_ is None
    assert isinstance(mlp_estimator.validation_scores_, list)

    valid_scores = mlp_estimator.validation_scores_
    best_valid_score = mlp_estimator.best_validation_score_
    assert max(valid_scores) == best_valid_score
    assert best_valid_score + tol > valid_scores[-2]
    assert best_valid_score + tol > valid_scores[-1]

    # check that the attributes `validation_scores_` and `best_validation_score_`
    # are set to None when `early_stopping=False`
    mlp_estimator = MLPEstimator(
        tol=tol, max_iter=3000, solver="sgd", early_stopping=False
    )
    mlp_estimator.fit(X, y)
    assert mlp_estimator.validation_scores_ is None
    assert mlp_estimator.best_validation_score_ is None
    assert mlp_estimator.best_loss_ is not None