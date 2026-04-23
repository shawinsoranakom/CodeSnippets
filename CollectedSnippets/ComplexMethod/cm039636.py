def test_lasso_lars_vs_lasso_cd_positive():
    # Test that LassoLars and Lasso using coordinate descent give the
    # same results when using the positive option

    # This test is basically a copy of the above with additional positive
    # option. However for the middle part, the comparison of coefficient values
    # for a range of alphas, we had to make an adaptations. See below.

    # not normalized data
    X = 3 * diabetes.data

    alphas, _, lasso_path = linear_model.lars_path(X, y, method="lasso", positive=True)
    lasso_cd = linear_model.Lasso(fit_intercept=False, tol=1e-8, positive=True)
    for c, a in zip(lasso_path.T, alphas):
        if a == 0:
            continue
        lasso_cd.alpha = a
        lasso_cd.fit(X, y)
        error = linalg.norm(c - lasso_cd.coef_)
        assert error < 0.01

    # The range of alphas chosen for coefficient comparison here is restricted
    # as compared with the above test without the positive option. This is due
    # to the circumstance that the Lars-Lasso algorithm does not converge to
    # the least-squares-solution for small alphas, see 'Least Angle Regression'
    # by Efron et al 2004. The coefficients are typically in congruence up to
    # the smallest alpha reached by the Lars-Lasso algorithm and start to
    # diverge thereafter.  See
    # https://gist.github.com/michigraber/7e7d7c75eca694c7a6ff

    for alpha in np.linspace(6e-1, 1 - 1e-2, 20):
        clf1 = linear_model.LassoLars(
            fit_intercept=False, alpha=alpha, positive=True
        ).fit(X, y)
        clf2 = linear_model.Lasso(
            fit_intercept=False, alpha=alpha, tol=1e-8, positive=True
        ).fit(X, y)
        err = linalg.norm(clf1.coef_ - clf2.coef_)
        assert err < 1e-3

    # normalized data
    X = diabetes.data - diabetes.data.sum(axis=0)
    X /= np.linalg.norm(X, axis=0)
    alphas, _, lasso_path = linear_model.lars_path(X, y, method="lasso", positive=True)
    lasso_cd = linear_model.Lasso(fit_intercept=False, tol=1e-8, positive=True)
    for c, a in zip(lasso_path.T[:-1], alphas[:-1]):  # don't include alpha=0
        lasso_cd.alpha = a
        lasso_cd.fit(X, y)
        error = linalg.norm(c - lasso_cd.coef_)
        assert error < 0.01