def test_oob_multilcass_iris():
    # Check OOB improvement on multi-class dataset.
    estimator = GradientBoostingClassifier(
        n_estimators=100, loss="log_loss", random_state=1, subsample=0.5
    )
    estimator.fit(iris.data, iris.target)
    score = estimator.score(iris.data, iris.target)
    assert score > 0.9
    assert estimator.oob_improvement_.shape[0] == estimator.n_estimators
    assert estimator.oob_scores_.shape[0] == estimator.n_estimators
    assert estimator.oob_scores_[-1] == pytest.approx(estimator.oob_score_)

    estimator = GradientBoostingClassifier(
        n_estimators=100,
        loss="log_loss",
        random_state=1,
        subsample=0.5,
        n_iter_no_change=5,
    )
    estimator.fit(iris.data, iris.target)
    score = estimator.score(iris.data, iris.target)
    assert estimator.oob_improvement_.shape[0] < estimator.n_estimators
    assert estimator.oob_scores_.shape[0] < estimator.n_estimators
    assert estimator.oob_scores_[-1] == pytest.approx(estimator.oob_score_)