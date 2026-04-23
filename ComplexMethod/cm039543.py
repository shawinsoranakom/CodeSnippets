def test_curve_scorer_pos_label(global_random_seed):
    """Check that we propagate properly the `pos_label` parameter to the scorer."""
    n_samples = 30
    X, y = make_classification(
        n_samples=n_samples, weights=[0.9, 0.1], random_state=global_random_seed
    )
    estimator = LogisticRegression().fit(X, y)

    curve_scorer = _CurveScorer(
        recall_score,
        sign=1,
        response_method="predict_proba",
        thresholds=10,
        kwargs={"pos_label": 1},
    )
    scores_pos_label_1, thresholds_pos_label_1 = curve_scorer(estimator, X, y)

    curve_scorer = _CurveScorer(
        recall_score,
        sign=1,
        response_method="predict_proba",
        thresholds=10,
        kwargs={"pos_label": 0},
    )
    scores_pos_label_0, thresholds_pos_label_0 = curve_scorer(estimator, X, y)

    # Since `pos_label` is forwarded to the curve_scorer, the thresholds are not equal.
    assert not (thresholds_pos_label_1 == thresholds_pos_label_0).all()
    # The min-max range for the thresholds is defined by the probabilities of the
    # `pos_label` class (the column of `predict_proba`).
    y_pred = estimator.predict_proba(X)
    assert thresholds_pos_label_0.min() == pytest.approx(y_pred.min(axis=0)[0])
    assert thresholds_pos_label_0.max() == pytest.approx(y_pred.max(axis=0)[0])
    assert thresholds_pos_label_1.min() == pytest.approx(y_pred.min(axis=0)[1])
    assert thresholds_pos_label_1.max() == pytest.approx(y_pred.max(axis=0)[1])

    # The recall cannot be negative and `pos_label=1` should have a higher recall
    # since there is less samples to be considered.
    assert 0.0 < scores_pos_label_0.min() < scores_pos_label_1.min()
    assert scores_pos_label_0.max() == pytest.approx(1.0)
    assert scores_pos_label_1.max() == pytest.approx(1.0)