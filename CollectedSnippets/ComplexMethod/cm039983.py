def _nls_subproblem(
    X, W, H, tol, max_iter, alpha=0.0, l1_ratio=0.0, sigma=0.01, beta=0.1
):
    """Non-negative least square solver
    Solves a non-negative least squares subproblem using the projected
    gradient descent algorithm.
    Parameters
    ----------
    X : array-like, shape (n_samples, n_features)
        Constant matrix.
    W : array-like, shape (n_samples, n_components)
        Constant matrix.
    H : array-like, shape (n_components, n_features)
        Initial guess for the solution.
    tol : float
        Tolerance of the stopping condition.
    max_iter : int
        Maximum number of iterations before timing out.
    alpha : double, default: 0.
        Constant that multiplies the regularization terms. Set it to zero to
        have no regularization.
    l1_ratio : double, default: 0.
        The regularization mixing parameter, with 0 <= l1_ratio <= 1.
        For l1_ratio = 0 the penalty is an L2 penalty.
        For l1_ratio = 1 it is an L1 penalty.
        For 0 < l1_ratio < 1, the penalty is a combination of L1 and L2.
    sigma : float
        Constant used in the sufficient decrease condition checked by the line
        search.  Smaller values lead to a looser sufficient decrease condition,
        thus reducing the time taken by the line search, but potentially
        increasing the number of iterations of the projected gradient
        procedure. 0.01 is a commonly used value in the optimization
        literature.
    beta : float
        Factor by which the step size is decreased (resp. increased) until
        (resp. as long as) the sufficient decrease condition is satisfied.
        Larger values allow to find a better step size but lead to longer line
        search. 0.1 is a commonly used value in the optimization literature.
    Returns
    -------
    H : array-like, shape (n_components, n_features)
        Solution to the non-negative least squares problem.
    grad : array-like, shape (n_components, n_features)
        The gradient.
    n_iter : int
        The number of iterations done by the algorithm.
    References
    ----------
    C.-J. Lin. Projected gradient methods for non-negative matrix
    factorization. Neural Computation, 19(2007), 2756-2779.
    https://www.csie.ntu.edu.tw/~cjlin/nmf/
    """
    WtX = safe_sparse_dot(W.T, X)
    WtW = np.dot(W.T, W)

    # values justified in the paper (alpha is renamed gamma)
    gamma = 1
    for n_iter in range(1, max_iter + 1):
        grad = np.dot(WtW, H) - WtX
        if alpha > 0 and l1_ratio == 1.0:
            grad += alpha
        elif alpha > 0:
            grad += alpha * (l1_ratio + (1 - l1_ratio) * H)

        # The following multiplication with a boolean array is more than twice
        # as fast as indexing into grad.
        if _norm(grad * np.logical_or(grad < 0, H > 0)) < tol:
            break

        Hp = H

        for inner_iter in range(20):
            # Gradient step.
            Hn = H - gamma * grad
            # Projection step.
            Hn *= Hn > 0
            d = Hn - H
            gradd = np.dot(grad.ravel(), d.ravel())
            dQd = np.dot(np.dot(WtW, d).ravel(), d.ravel())
            suff_decr = (1 - sigma) * gradd + 0.5 * dQd < 0
            if inner_iter == 0:
                decr_gamma = not suff_decr

            if decr_gamma:
                if suff_decr:
                    H = Hn
                    break
                else:
                    gamma *= beta
            elif not suff_decr or (Hp == Hn).all():
                H = Hp
                break
            else:
                gamma /= beta
                Hp = Hn

    if n_iter == max_iter:
        warnings.warn("Iteration limit reached in nls subproblem.", ConvergenceWarning)

    return H, grad, n_iter