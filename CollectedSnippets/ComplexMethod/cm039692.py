def check_cross_validate_single_metric(clf, X, y, scores, cv):
    (
        train_mse_scores,
        test_mse_scores,
        train_r2_scores,
        test_r2_scores,
        fitted_estimators,
    ) = scores
    # Test single metric evaluation when scoring is string or singleton list
    for return_train_score, dict_len in ((True, 4), (False, 3)):
        # Single metric passed as a string
        if return_train_score:
            mse_scores_dict = cross_validate(
                clf,
                X,
                y,
                scoring="neg_mean_squared_error",
                return_train_score=True,
                cv=cv,
            )
            assert_array_almost_equal(mse_scores_dict["train_score"], train_mse_scores)
        else:
            mse_scores_dict = cross_validate(
                clf,
                X,
                y,
                scoring="neg_mean_squared_error",
                return_train_score=False,
                cv=cv,
            )
        assert isinstance(mse_scores_dict, dict)
        assert len(mse_scores_dict) == dict_len
        assert_array_almost_equal(mse_scores_dict["test_score"], test_mse_scores)

        # Single metric passed as a list
        if return_train_score:
            # It must be True by default - deprecated
            r2_scores_dict = cross_validate(
                clf, X, y, scoring=["r2"], return_train_score=True, cv=cv
            )
            assert_array_almost_equal(r2_scores_dict["train_r2"], train_r2_scores, True)
        else:
            r2_scores_dict = cross_validate(
                clf, X, y, scoring=["r2"], return_train_score=False, cv=cv
            )
        assert isinstance(r2_scores_dict, dict)
        assert len(r2_scores_dict) == dict_len
        assert_array_almost_equal(r2_scores_dict["test_r2"], test_r2_scores)

    # Test return_estimator option
    mse_scores_dict = cross_validate(
        clf, X, y, scoring="neg_mean_squared_error", return_estimator=True, cv=cv
    )
    for k, est in enumerate(mse_scores_dict["estimator"]):
        est_coef = est.coef_.copy()
        if issparse(est_coef):
            est_coef = est_coef.toarray()

        fitted_est_coef = fitted_estimators[k].coef_.copy()
        if issparse(fitted_est_coef):
            fitted_est_coef = fitted_est_coef.toarray()

        assert_almost_equal(est_coef, fitted_est_coef)
        assert_almost_equal(est.intercept_, fitted_estimators[k].intercept_)