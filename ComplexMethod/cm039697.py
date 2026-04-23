def test_cross_validate_failing_scorer(
    error_score, return_train_score, with_multimetric
):
    # Check that an estimator can fail during scoring in `cross_validate` and
    # that we can optionally replace it with `error_score`. In the multimetric
    # case also check the result of a non-failing scorer where the other scorers
    # are failing.
    X, y = load_iris(return_X_y=True)
    clf = LogisticRegression(max_iter=5).fit(X, y)

    error_msg = "This scorer is supposed to fail!!!"
    failing_scorer = partial(_failing_scorer, error_msg=error_msg)
    if with_multimetric:
        non_failing_scorer = make_scorer(mean_squared_error)
        scoring = {
            "score_1": failing_scorer,
            "score_2": non_failing_scorer,
            "score_3": failing_scorer,
        }
    else:
        scoring = failing_scorer

    if error_score == "raise":
        with pytest.raises(ValueError, match=error_msg):
            cross_validate(
                clf,
                X,
                y,
                cv=3,
                scoring=scoring,
                return_train_score=return_train_score,
                error_score=error_score,
            )
    else:
        warning_msg = (
            "Scoring failed. The score on this train-test partition for "
            f"these parameters will be set to {error_score}"
        )
        with pytest.warns(UserWarning, match=warning_msg):
            results = cross_validate(
                clf,
                X,
                y,
                cv=3,
                scoring=scoring,
                return_train_score=return_train_score,
                error_score=error_score,
            )
            for key in results:
                if "_score" in key:
                    if "_score_2" in key:
                        # check the test (and optionally train) score for the
                        # scorer that should be non-failing
                        for i in results[key]:
                            assert isinstance(i, float)
                    else:
                        # check the test (and optionally train) score for all
                        # scorers that should be assigned to `error_score`.
                        assert_allclose(results[key], error_score)