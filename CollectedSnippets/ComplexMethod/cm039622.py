def test_check_solver_option(LR):
    X, y = iris.data, iris.target

    # only 'liblinear' solver
    for solver in ["liblinear"]:
        msg = f"The '{solver}' solver does not support multiclass classification."
        lr = LR(solver=solver)
        with pytest.raises(ValueError, match=msg):
            lr.fit(X, y)

    # all solvers except 'liblinear' and 'saga'
    for solver in ["lbfgs", "newton-cg", "newton-cholesky", "sag"]:
        msg = "Solver %s supports only 'l2' or None penalties," % solver
        if LR == LogisticRegression:
            lr = LR(solver=solver, l1_ratio=1)
        else:
            lr = LR(solver=solver, l1_ratios=(1,))
        with pytest.raises(ValueError, match=msg):
            lr.fit(X, y)
    for solver in ["lbfgs", "newton-cg", "newton-cholesky", "sag", "saga"]:
        msg = "Solver %s supports only dual=False, got dual=True" % solver
        lr = LR(solver=solver, dual=True)
        with pytest.raises(ValueError, match=msg):
            lr.fit(X, y)

    # only saga supports elasticnet. We only test for liblinear because the
    # error is raised before for the other solvers (solver %s supports only l2
    # penalties)
    for solver in ["liblinear"]:
        msg = f"Only 'saga' solver supports elasticnet penalty, got solver={solver}."
        if LR == LogisticRegression:
            lr = LR(solver=solver, l1_ratio=0.5)
        else:
            lr = LR(solver=solver, l1_ratios=(0.5,))
        with pytest.raises(ValueError, match=msg):
            lr.fit(X, y)

    # liblinear does not support penalty='none'
    # (LogisticRegressionCV does not supports penalty='none' at all)
    if LR is LogisticRegression:
        msg = "penalty=None is not supported for the liblinear solver"
        lr = LR(C=np.inf, solver="liblinear")
        with pytest.raises(ValueError, match=msg):
            lr.fit(X, y)