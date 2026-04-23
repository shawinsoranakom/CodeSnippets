def test_dtype_match(solver, fit_intercept, csr_container):
    # Test that np.float32 input data is not cast to np.float64 when possible
    # and that the output is approximately the same no matter the input format.

    out32_type = np.float64 if solver == "liblinear" else np.float32

    X_32 = np.array(X).astype(np.float32)
    y_32 = np.array(Y1).astype(np.float32)
    X_64 = np.array(X).astype(np.float64)
    y_64 = np.array(Y1).astype(np.float64)
    X_sparse_32 = csr_container(X, dtype=np.float32)
    X_sparse_64 = csr_container(X, dtype=np.float64)
    solver_tol = 5e-4

    lr_templ = LogisticRegression(
        solver=solver,
        random_state=42,
        tol=solver_tol,
        fit_intercept=fit_intercept,
    )

    # Check 32-bit type consistency
    lr_32 = clone(lr_templ)
    lr_32.fit(X_32, y_32)
    assert lr_32.coef_.dtype == out32_type

    # Check 32-bit type consistency with sparsity
    lr_32_sparse = clone(lr_templ)
    lr_32_sparse.fit(X_sparse_32, y_32)
    assert lr_32_sparse.coef_.dtype == out32_type

    # Check 64-bit type consistency
    lr_64 = clone(lr_templ)
    lr_64.fit(X_64, y_64)
    assert lr_64.coef_.dtype == np.float64

    # Check 64-bit type consistency with sparsity
    lr_64_sparse = clone(lr_templ)
    lr_64_sparse.fit(X_sparse_64, y_64)
    assert lr_64_sparse.coef_.dtype == np.float64

    # solver_tol bounds the norm of the loss gradient
    # dw ~= inv(H)*grad ==> |dw| ~= |inv(H)| * solver_tol, where H - hessian
    #
    # See https://github.com/scikit-learn/scikit-learn/pull/13645
    #
    # with  Z = np.hstack((np.ones((3,1)), np.array(X)))
    # In [8]: np.linalg.norm(np.diag([0,2,2]) + np.linalg.inv((Z.T @ Z)/4))
    # Out[8]: 1.7193336918135917

    # factor of 2 to get the ball diameter
    atol = 2 * 1.72 * solver_tol
    if os.name == "nt" and _IS_32BIT:
        # FIXME
        atol = 1e-2

    # Check accuracy consistency
    assert_allclose(lr_32.coef_, lr_64.coef_.astype(np.float32), atol=atol)

    if solver in ("sag", "saga") and fit_intercept:
        # FIXME: SAGA on sparse data fits the intercept inaccurately with the
        # default tol and max_iter parameters.
        atol = 2e-1

    assert_allclose(lr_32.coef_, lr_32_sparse.coef_, atol=atol)
    assert_allclose(lr_64.coef_, lr_64_sparse.coef_, atol=atol)