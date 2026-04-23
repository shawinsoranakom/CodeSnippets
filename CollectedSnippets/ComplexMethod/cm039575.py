def orthogonal_mp(
    X,
    y,
    *,
    n_nonzero_coefs=None,
    tol=None,
    precompute=False,
    copy_X=True,
    return_path=False,
    return_n_iter=False,
):
    r"""Orthogonal Matching Pursuit (OMP).

    Solves n_targets Orthogonal Matching Pursuit problems.
    An instance of the problem has the form:

    When parametrized by the number of non-zero coefficients using
    `n_nonzero_coefs`:
    argmin ||y - X\gamma||^2 subject to ||\gamma||_0 <= n_{nonzero coefs}

    When parametrized by error using the parameter `tol`:
    argmin ||\gamma||_0 subject to ||y - X\gamma||^2 <= tol

    Read more in the :ref:`User Guide <omp>`.

    Parameters
    ----------
    X : array-like of shape (n_samples, n_features)
        Input data. Columns are assumed to have unit norm.

    y : ndarray of shape (n_samples,) or (n_samples, n_targets)
        Input targets.

    n_nonzero_coefs : int, default=None
        Desired number of non-zero entries in the solution. If None (by
        default) this value is set to 10% of n_features.

    tol : float, default=None
        Maximum squared norm of the residual. If not None, overrides n_nonzero_coefs.

    precompute : 'auto' or bool, default=False
        Whether to perform precomputations. Improves performance when n_targets
        or n_samples is very large.

    copy_X : bool, default=True
        Whether the design matrix X must be copied by the algorithm. A false
        value is only helpful if X is already Fortran-ordered, otherwise a
        copy is made anyway.

    return_path : bool, default=False
        Whether to return every value of the nonzero coefficients along the
        forward path. Useful for cross-validation.

    return_n_iter : bool, default=False
        Whether or not to return the number of iterations.

    Returns
    -------
    coef : ndarray of shape (n_features,) or (n_features, n_targets)
        Coefficients of the OMP solution. If `return_path=True`, this contains
        the whole coefficient path. In this case its shape is
        (n_features, n_features) or (n_features, n_targets, n_features) and
        iterating over the last axis generates coefficients in increasing order
        of active features.

    n_iters : array-like or int
        Number of active features across every target. Returned only if
        `return_n_iter` is set to True.

    See Also
    --------
    OrthogonalMatchingPursuit : Orthogonal Matching Pursuit model.
    orthogonal_mp_gram : Solve OMP problems using Gram matrix and the product X.T * y.
    lars_path : Compute Least Angle Regression or Lasso path using LARS algorithm.
    sklearn.decomposition.sparse_encode : Sparse coding.

    Notes
    -----
    Orthogonal matching pursuit was introduced in S. Mallat, Z. Zhang,
    Matching pursuits with time-frequency dictionaries, IEEE Transactions on
    Signal Processing, Vol. 41, No. 12. (December 1993), pp. 3397-3415.
    (https://www.di.ens.fr/~mallat/papiers/MallatPursuit93.pdf)

    This implementation is based on Rubinstein, R., Zibulevsky, M. and Elad,
    M., Efficient Implementation of the K-SVD Algorithm using Batch Orthogonal
    Matching Pursuit Technical Report - CS Technion, April 2008.
    https://www.cs.technion.ac.il/~ronrubin/Publications/KSVD-OMP-v2.pdf

    Examples
    --------
    >>> from sklearn.datasets import make_regression
    >>> from sklearn.linear_model import orthogonal_mp
    >>> X, y = make_regression(noise=4, random_state=0)
    >>> coef = orthogonal_mp(X, y)
    >>> coef.shape
    (100,)
    >>> X[:1,] @ coef
    array([-78.68])
    """
    X = check_array(X, order="F", copy=copy_X)
    copy_X = False
    if y.ndim == 1:
        y = y.reshape(-1, 1)
    y = check_array(y)
    if y.shape[1] > 1:  # subsequent targets will be affected
        copy_X = True
    if n_nonzero_coefs is None and tol is None:
        # default for n_nonzero_coefs is 0.1 * n_features
        # but at least one.
        n_nonzero_coefs = max(int(0.1 * X.shape[1]), 1)
    if tol is None and n_nonzero_coefs > X.shape[1]:
        raise ValueError(
            "The number of atoms cannot be more than the number of features"
        )
    if precompute == "auto":
        precompute = X.shape[0] > X.shape[1]
    if precompute:
        G = np.dot(X.T, X)
        G = np.asfortranarray(G)
        Xy = np.dot(X.T, y)
        if tol is not None:
            norms_squared = np.sum((y**2), axis=0)
        else:
            norms_squared = None
        return orthogonal_mp_gram(
            G,
            Xy,
            n_nonzero_coefs=n_nonzero_coefs,
            tol=tol,
            norms_squared=norms_squared,
            copy_Gram=copy_X,
            copy_Xy=False,
            return_path=return_path,
        )

    if return_path:
        coef = np.zeros((X.shape[1], y.shape[1], X.shape[1]))
    else:
        coef = np.zeros((X.shape[1], y.shape[1]))
    n_iters = []

    for k in range(y.shape[1]):
        out = _cholesky_omp(
            X, y[:, k], n_nonzero_coefs, tol, copy_X=copy_X, return_path=return_path
        )
        if return_path:
            _, idx, coefs, n_iter = out
            coef = coef[:, :, : len(idx)]
            for n_active, x in enumerate(coefs.T):
                coef[idx[: n_active + 1], k, n_active] = x[: n_active + 1]
        else:
            x, idx, n_iter = out
            coef[idx, k] = x
        n_iters.append(n_iter)

    if y.shape[1] == 1:
        n_iters = n_iters[0]

    if return_n_iter:
        return np.squeeze(coef), n_iters
    else:
        return np.squeeze(coef)