def test_newton_solver_verbosity(capsys, verbose):
    """Test the std output of verbose newton solvers."""
    y = np.array([1, 2], dtype=float)
    X = np.array([[1.0, 0], [0, 1]], dtype=float)
    linear_loss = LinearModelLoss(base_loss=HalfPoissonLoss(), fit_intercept=False)
    sol = NewtonCholeskySolver(
        coef=linear_loss.init_zero_coef(X),
        linear_loss=linear_loss,
        l2_reg_strength=0,
        verbose=verbose,
    )
    sol.solve(X, y, None)  # returns array([0., 0.69314758])
    captured = capsys.readouterr()

    if verbose == 0:
        assert captured.out == ""
    else:
        msg = [
            "Newton iter=1",
            "Check Convergence",
            "1. max |gradient|",
            "2. Newton decrement",
            "Solver did converge at loss = ",
        ]
        for m in msg:
            assert m in captured.out

    if verbose >= 2:
        msg = ["Backtracking Line Search", "line search iteration="]
        for m in msg:
            assert m in captured.out

    # Set the Newton solver to a state with a completely wrong Newton step.
    sol = NewtonCholeskySolver(
        coef=linear_loss.init_zero_coef(X),
        linear_loss=linear_loss,
        l2_reg_strength=0,
        verbose=verbose,
    )
    sol.setup(X=X, y=y, sample_weight=None)
    sol.iteration = 1
    sol.update_gradient_hessian(X=X, y=y, sample_weight=None)
    sol.coef_newton = np.array([1.0, 0])
    sol.gradient_times_newton = sol.gradient @ sol.coef_newton
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        sol.line_search(X=X, y=y, sample_weight=None)
        captured = capsys.readouterr()
    if verbose >= 1:
        assert (
            "Line search did not converge and resorts to lbfgs instead." in captured.out
        )

    # Set the Newton solver to a state with bad Newton step such that the loss
    # improvement in line search is tiny.
    sol = NewtonCholeskySolver(
        coef=np.array([1e-12, 0.69314758]),
        linear_loss=linear_loss,
        l2_reg_strength=0,
        verbose=verbose,
    )
    sol.setup(X=X, y=y, sample_weight=None)
    sol.iteration = 1
    sol.update_gradient_hessian(X=X, y=y, sample_weight=None)
    sol.coef_newton = np.array([1e-6, 0])
    sol.gradient_times_newton = sol.gradient @ sol.coef_newton
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        sol.line_search(X=X, y=y, sample_weight=None)
        captured = capsys.readouterr()
    if verbose >= 2:
        msg = [
            "line search iteration=",
            "check loss improvement <= armijo term:",
            "check loss |improvement| <= eps * |loss_old|:",
            "check sum(|gradient|) < sum(|gradient_old|):",
        ]
        for m in msg:
            assert m in captured.out

    # Test for a case with negative hessian. We badly initialize coef for a Tweedie
    # loss with non-canonical link, e.g. Inverse Gaussian deviance with a log link.
    linear_loss = LinearModelLoss(
        base_loss=HalfTweedieLoss(power=3), fit_intercept=False
    )
    sol = NewtonCholeskySolver(
        coef=linear_loss.init_zero_coef(X) + 1,
        linear_loss=linear_loss,
        l2_reg_strength=0,
        verbose=verbose,
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        sol.solve(X, y, None)
    captured = capsys.readouterr()
    if verbose >= 1:
        assert (
            "The inner solver detected a pointwise Hessian with many negative values"
            " and resorts to lbfgs instead." in captured.out
        )