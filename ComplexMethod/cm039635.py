def test_lasso_lars_vs_lasso_cd():
    # Test that LassoLars and Lasso using coordinate descent give the
    # same results.
    X = 3 * diabetes.data

    alphas, _, lasso_path = linear_model.lars_path(X, y, method="lasso")
    lasso_cd = linear_model.Lasso(fit_intercept=False, tol=1e-8)
    for c, a in zip(lasso_path.T, alphas):
        if a == 0:
            continue
        lasso_cd.alpha = a
        lasso_cd.fit(X, y)
        error = linalg.norm(c - lasso_cd.coef_)
        assert error < 0.01

    # similar test, with the classifiers
    for alpha in np.linspace(1e-2, 1 - 1e-2, 20):
        clf1 = linear_model.LassoLars(alpha=alpha).fit(X, y)
        clf2 = linear_model.Lasso(alpha=alpha, tol=1e-8).fit(X, y)
        err = linalg.norm(clf1.coef_ - clf2.coef_)
        assert err < 1e-3

    # same test, with normalized data
    X = diabetes.data
    X = X - X.sum(axis=0)
    X /= np.linalg.norm(X, axis=0)
    alphas, _, lasso_path = linear_model.lars_path(X, y, method="lasso")
    lasso_cd = linear_model.Lasso(fit_intercept=False, tol=1e-8)
    for c, a in zip(lasso_path.T, alphas):
        if a == 0:
            continue
        lasso_cd.alpha = a
        lasso_cd.fit(X, y)
        error = linalg.norm(c - lasso_cd.coef_)
        assert error < 0.01