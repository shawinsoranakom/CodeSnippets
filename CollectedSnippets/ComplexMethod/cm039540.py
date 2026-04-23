def test_check_scoring_and_check_multimetric_scoring(scoring):
    check_scoring_validator_for_single_metric_usecases(check_scoring)
    # To make sure the check_scoring is correctly applied to the constituent
    # scorers

    estimator = LinearSVC(random_state=0)
    estimator.fit([[1], [2], [3]], [1, 1, 0])

    scorers = _check_multimetric_scoring(estimator, scoring)
    assert isinstance(scorers, dict)
    assert sorted(scorers.keys()) == sorted(list(scoring))
    assert all([isinstance(scorer, _Scorer) for scorer in list(scorers.values())])
    assert all(scorer._response_method == "predict" for scorer in scorers.values())

    if "acc" in scoring:
        assert_almost_equal(
            scorers["acc"](estimator, [[1], [2], [3]], [1, 0, 0]), 2.0 / 3.0
        )
    if "accuracy" in scoring:
        assert_almost_equal(
            scorers["accuracy"](estimator, [[1], [2], [3]], [1, 0, 0]), 2.0 / 3.0
        )
    if "precision" in scoring:
        assert_almost_equal(
            scorers["precision"](estimator, [[1], [2], [3]], [1, 0, 0]), 0.5
        )