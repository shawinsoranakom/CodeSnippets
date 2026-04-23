def check_cross_validate_multi_metric(clf, X, y, scores, cv):
    # Test multimetric evaluation when scoring is a list / dict
    (
        train_mse_scores,
        test_mse_scores,
        train_r2_scores,
        test_r2_scores,
        fitted_estimators,
    ) = scores

    def custom_scorer(clf, X, y):
        y_pred = clf.predict(X)
        return {
            "r2": r2_score(y, y_pred),
            "neg_mean_squared_error": -mean_squared_error(y, y_pred),
        }

    all_scoring = (
        ("r2", "neg_mean_squared_error"),
        {
            "r2": make_scorer(r2_score),
            "neg_mean_squared_error": "neg_mean_squared_error",
        },
        custom_scorer,
    )

    keys_sans_train = {
        "test_r2",
        "test_neg_mean_squared_error",
        "fit_time",
        "score_time",
    }
    keys_with_train = keys_sans_train.union(
        {"train_r2", "train_neg_mean_squared_error"}
    )

    for return_train_score in (True, False):
        for scoring in all_scoring:
            if return_train_score:
                # return_train_score must be True by default - deprecated
                cv_results = cross_validate(
                    clf, X, y, scoring=scoring, return_train_score=True, cv=cv
                )
                assert_array_almost_equal(cv_results["train_r2"], train_r2_scores)
                assert_array_almost_equal(
                    cv_results["train_neg_mean_squared_error"], train_mse_scores
                )
            else:
                cv_results = cross_validate(
                    clf, X, y, scoring=scoring, return_train_score=False, cv=cv
                )
            assert isinstance(cv_results, dict)
            assert set(cv_results.keys()) == (
                keys_with_train if return_train_score else keys_sans_train
            )
            assert_array_almost_equal(cv_results["test_r2"], test_r2_scores)
            assert_array_almost_equal(
                cv_results["test_neg_mean_squared_error"], test_mse_scores
            )

            # Make sure all the arrays are of np.ndarray type
            assert isinstance(cv_results["test_r2"], np.ndarray)
            assert isinstance(cv_results["test_neg_mean_squared_error"], np.ndarray)
            assert isinstance(cv_results["fit_time"], np.ndarray)
            assert isinstance(cv_results["score_time"], np.ndarray)

            # Ensure all the times are within sane limits
            assert np.all(cv_results["fit_time"] >= 0)
            assert np.all(cv_results["fit_time"] < 10)
            assert np.all(cv_results["score_time"] >= 0)
            assert np.all(cv_results["score_time"] < 10)