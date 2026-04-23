def test_monitor_early_stopping(Cls):
    # Test if monitor return value works.
    X, y = datasets.make_hastie_10_2(n_samples=100, random_state=1)

    est = Cls(n_estimators=20, max_depth=1, random_state=1, subsample=0.5)
    est.fit(X, y, monitor=early_stopping_monitor)
    assert est.n_estimators == 20  # this is not altered
    assert est.estimators_.shape[0] == 10
    assert est.train_score_.shape[0] == 10
    assert est.oob_improvement_.shape[0] == 10
    assert est.oob_scores_.shape[0] == 10
    assert est.oob_scores_[-1] == pytest.approx(est.oob_score_)

    # try refit
    est.set_params(n_estimators=30)
    est.fit(X, y)
    assert est.n_estimators == 30
    assert est.estimators_.shape[0] == 30
    assert est.train_score_.shape[0] == 30
    assert est.oob_improvement_.shape[0] == 30
    assert est.oob_scores_.shape[0] == 30
    assert est.oob_scores_[-1] == pytest.approx(est.oob_score_)

    est = Cls(
        n_estimators=20, max_depth=1, random_state=1, subsample=0.5, warm_start=True
    )
    est.fit(X, y, monitor=early_stopping_monitor)
    assert est.n_estimators == 20
    assert est.estimators_.shape[0] == 10
    assert est.train_score_.shape[0] == 10
    assert est.oob_improvement_.shape[0] == 10
    assert est.oob_scores_.shape[0] == 10
    assert est.oob_scores_[-1] == pytest.approx(est.oob_score_)

    # try refit
    est.set_params(n_estimators=30, warm_start=False)
    est.fit(X, y)
    assert est.n_estimators == 30
    assert est.train_score_.shape[0] == 30
    assert est.estimators_.shape[0] == 30
    assert est.oob_improvement_.shape[0] == 30
    assert est.oob_scores_.shape[0] == 30
    assert est.oob_scores_[-1] == pytest.approx(est.oob_score_)