def orthogonal_mp_gram(
    Gram,
    Xy,
    *,
    n_nonzero_coefs=None,
    tol=None,
    norms_squared=None,
    copy_Gram=True,
    copy_Xy=True,
    return_path=False,
    return_n_iter=False,
):
    """Gram Orthogonal Matching Pursuit (OMP).

    Solves n_targets Orthogonal Matching Pursuit problems using only
    the Gram matrix X.T * X and the product X.T * y.

    Read more in the :ref:`User Guide <omp>`.

    Parameters
    ----------
    Gram : array-like of shape (n_features, n_features)
        Gram matrix of the input data: `X.T * X`.

    Xy : array-like of shape (n_features,) or (n_features, n_targets)
        Input targets multiplied by `X`: `X.T * y`.

    n_nonzero_coefs : int, default=None
        Desired number of non-zero entries in the solution. If `None` (by
        default) this value is set to 10% of n_features.

    tol : float, default=None
        Maximum squared norm of the residual. If not `None`,
        overrides `n_nonzero_coefs`.

    norms_squared : array-like of shape (n_targets,), default=None
        Squared L2 norms of the lines of `y`. Required if `tol` is not None.

    copy_Gram : bool, default=True
        Whether the gram matrix must be copied by the algorithm. A `False`
        value is only helpful if it is already Fortran-ordered, otherwise a
        copy is made anyway.

    copy_Xy : bool, default=True
        Whether the covariance vector `Xy` must be copied by the algorithm.
        If `False`, it may be overwritten.

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
        `(n_features, n_features)` or `(n_features, n_targets, n_features)` and
        iterating over the last axis yields coefficients in increasing order
        of active features.

    n_iters : list or int
        Number of active features across every target. Returned only if
        `return_n_iter` is set to True.

    See Also
    --------
    OrthogonalMatchingPursuit : Orthogonal Matching Pursuit model (OMP).
    orthogonal_mp : Solves n_targets Orthogonal Matching Pursuit problems.
    lars_path : Compute Least Angle Regression or Lasso path using
        LARS algorithm.
    sklearn.decomposition.sparse_encode : Generic sparse coding.
        Each column of the result is the solution to a Lasso problem.

    Notes
    -----
    Orthogonal matching pursuit was introduced in G. Mallat, Z. Zhang,
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
    >>> from sklearn.linear_model import orthogonal_mp_gram
    >>> X, y = make_regression(noise=4, random_state=0)
    >>> coef = orthogonal_mp_gram(X.T @ X, X.T @ y)
    >>> coef.shape
    (100,)
    >>> X[:1,] @ coef
    array([-78.68])
    """
    Gram = check_array(Gram, order="F", copy=copy_Gram)
    Xy = np.asarray(Xy)
    if Xy.ndim > 1 and Xy.shape[1] > 1:
        # or subsequent target will be affected
        copy_Gram = True
    if Xy.ndim == 1:
        Xy = Xy[:, np.newaxis]
        if tol is not None:
            norms_squared = [norms_squared]
    if copy_Xy or not Xy.flags.writeable:
        # Make the copy once instead of many times in _gram_omp itself.
        Xy = Xy.copy()

    if n_nonzero_coefs is None and tol is None:
        n_nonzero_coefs = int(0.1 * len(Gram))
    if tol is not None and norms_squared is None:
        raise ValueError(
            "Gram OMP needs the precomputed norms in order "
            "to evaluate the error sum of squares."
        )
    if tol is not None and tol < 0:
        raise ValueError("Epsilon cannot be negative")
    if tol is None and n_nonzero_coefs <= 0:
        raise ValueError("The number of atoms must be positive")
    if tol is None and n_nonzero_coefs > len(Gram):
        raise ValueError(
            "The number of atoms cannot be more than the number of features"
        )

    if return_path:
        coef = np.zeros((len(Gram), Xy.shape[1], len(Gram)), dtype=Gram.dtype)
    else:
        coef = np.zeros((len(Gram), Xy.shape[1]), dtype=Gram.dtype)

    n_iters = []
    for k in range(Xy.shape[1]):
        out = _gram_omp(
            Gram,
            Xy[:, k],
            n_nonzero_coefs,
            norms_squared[k] if tol is not None else None,
            tol,
            copy_Gram=copy_Gram,
            copy_Xy=False,
            return_path=return_path,
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

    if Xy.shape[1] == 1:
        n_iters = n_iters[0]

    if return_n_iter:
        return np.squeeze(coef), n_iters
    else:
        return np.squeeze(coef)