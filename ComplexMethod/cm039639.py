def test_multitask_enet_and_lasso_cv():
    X, y, _, _ = build_dataset(n_features=50, n_targets=3)
    clf = MultiTaskElasticNetCV(cv=3).fit(X, y)
    assert_almost_equal(clf.alpha_, 0.00556, 3)
    clf = MultiTaskLassoCV(cv=3, tol=1e-6).fit(X, y)
    assert_almost_equal(clf.alpha_, 0.00278, 3)

    X, y, _, _ = build_dataset(n_targets=3)
    clf = MultiTaskElasticNetCV(
        alphas=10, eps=1e-3, max_iter=200, l1_ratio=[0.3, 0.5], tol=1e-3, cv=3
    )
    clf.fit(X, y)
    assert 0.5 == clf.l1_ratio_
    assert (3, X.shape[1]) == clf.coef_.shape
    assert (3,) == clf.intercept_.shape
    assert (2, 10, 3) == clf.mse_path_.shape
    assert (2, 10) == clf.alphas_.shape

    X, y, _, _ = build_dataset(n_targets=3)
    clf = MultiTaskLassoCV(alphas=10, eps=1e-3, max_iter=500, tol=1e-3, cv=3)
    clf.fit(X, y)
    assert (3, X.shape[1]) == clf.coef_.shape
    assert (3,) == clf.intercept_.shape
    assert (10, 3) == clf.mse_path_.shape
    assert 10 == len(clf.alphas_)