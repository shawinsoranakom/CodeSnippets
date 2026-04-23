def _cg(fhess_p, fgrad, maxiter, tol, verbose=0):
    """
    Solve iteratively the linear system 'fhess_p . xsupi = fgrad'
    with a conjugate gradient descent.

    Parameters
    ----------
    fhess_p : callable
        Function that takes the gradient as a parameter and returns the
        matrix product of the Hessian and gradient.

    fgrad : ndarray of shape (n_features,) or (n_features + 1,)
        Gradient vector.

    maxiter : int
        Number of CG iterations.

    tol : float
        Stopping criterion.

    Returns
    -------
    xsupi : ndarray of shape (n_features,) or (n_features + 1,)
        Estimated solution.
    """
    eps = 16 * np.finfo(np.float64).eps
    xsupi = np.zeros(len(fgrad), dtype=fgrad.dtype)
    ri = np.copy(fgrad)  # residual = fgrad - fhess_p @ xsupi
    psupi = -ri
    i = 0
    dri0 = np.dot(ri, ri)
    # We also keep track of |p_i|^2.
    psupi_norm2 = dri0
    is_verbose = verbose >= 2

    while i <= maxiter:
        if np.sum(np.abs(ri)) <= tol:
            if is_verbose:
                print(
                    f"  Inner CG solver iteration {i} stopped with\n"
                    f"    sum(|residuals|) <= tol: {np.sum(np.abs(ri))} <= {tol}"
                )
            break

        Ap = fhess_p(psupi)
        # check curvature
        curv = np.dot(psupi, Ap)
        if 0 <= curv <= eps * psupi_norm2:
            # See https://arxiv.org/abs/1803.02924, Algo 1 Capped Conjugate Gradient.
            if is_verbose:
                print(
                    f"  Inner CG solver iteration {i} stopped with\n"
                    f"    tiny_|p| = eps * ||p||^2, eps = {eps}, "
                    f"squared L2 norm ||p||^2 = {psupi_norm2}\n"
                    f"    curvature <= tiny_|p|: {curv} <= {eps * psupi_norm2}"
                )
            break
        elif curv < 0:
            if i > 0:
                if is_verbose:
                    print(
                        f"  Inner CG solver iteration {i} stopped with negative "
                        f"curvature, curvature = {curv}"
                    )
                break
            else:
                # fall back to steepest descent direction
                xsupi += dri0 / curv * psupi
                if is_verbose:
                    print("  Inner CG solver iteration 0 fell back to steepest descent")
                break
        alphai = dri0 / curv
        xsupi += alphai * psupi
        ri += alphai * Ap
        dri1 = np.dot(ri, ri)
        betai = dri1 / dri0
        psupi = -ri + betai * psupi
        # We use  |p_i|^2 = |r_i|^2 + beta_i^2 |p_{i-1}|^2
        psupi_norm2 = dri1 + betai**2 * psupi_norm2
        i = i + 1
        dri0 = dri1  # update np.dot(ri,ri) for next time.
    if is_verbose and i > maxiter:
        print(
            f"  Inner CG solver stopped reaching maxiter={i - 1} with "
            f"sum(|residuals|) = {np.sum(np.abs(ri))}"
        )
    return xsupi