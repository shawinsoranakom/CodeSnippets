def _compute_precision_cholesky(covariances, covariance_type, xp=None):
    """Compute the Cholesky decomposition of the precisions.

    Parameters
    ----------
    covariances : array-like
        The covariance matrix of the current components.
        The shape depends of the covariance_type.

    covariance_type : {'full', 'tied', 'diag', 'spherical'}
        The type of precision matrices.

    Returns
    -------
    precisions_cholesky : array-like
        The Cholesky decomposition of sample precisions of the current
        components. The shape depends of the covariance_type.
    """
    xp, _, device_ = get_namespace_and_device(covariances, xp=xp)

    estimate_precision_error_message = (
        "Fitting the mixture model failed because some components have "
        "ill-defined empirical covariance (for instance caused by singleton "
        "or collapsed samples). Try to decrease the number of components, "
        "increase reg_covar, or scale the input data."
    )
    dtype = covariances.dtype
    if dtype == xp.float32:
        estimate_precision_error_message += (
            " The numerical accuracy can also be improved by passing float64"
            " data instead of float32."
        )

    if covariance_type == "full":
        n_components, n_features, _ = covariances.shape
        precisions_chol = xp.empty(
            (n_components, n_features, n_features), device=device_, dtype=dtype
        )
        for k in range(covariances.shape[0]):
            covariance = covariances[k, :, :]
            try:
                cov_chol = _cholesky(covariance, xp)
            # catch only numpy exceptions, b/c exceptions aren't part of array api spec
            except np.linalg.LinAlgError:
                raise ValueError(estimate_precision_error_message)
            precisions_chol[k, :, :] = _linalg_solve(
                cov_chol, xp.eye(n_features, dtype=dtype, device=device_), xp
            ).T
    elif covariance_type == "tied":
        _, n_features = covariances.shape
        try:
            cov_chol = _cholesky(covariances, xp)
        # catch only numpy exceptions, since exceptions are not part of array api spec
        except np.linalg.LinAlgError:
            raise ValueError(estimate_precision_error_message)
        precisions_chol = _linalg_solve(
            cov_chol, xp.eye(n_features, dtype=dtype, device=device_), xp
        ).T
    else:
        if xp.any(covariances <= 0.0):
            raise ValueError(estimate_precision_error_message)
        precisions_chol = 1.0 / xp.sqrt(covariances)
    return precisions_chol