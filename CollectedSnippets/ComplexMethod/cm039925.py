def count_nonzero(X, axis=None, sample_weight=None):
    """A variant of X.getnnz() with extension to weighting on axis 0.

    Useful in efficiently calculating multilabel metrics.

    Parameters
    ----------
    X : sparse matrix of shape (n_samples, n_labels)
        Input data. It should be of CSR format.

    axis : {0, 1}, default=None
        The axis on which the data is aggregated.

    sample_weight : array-like of shape (n_samples,), default=None
        Weight for each row of X.

    Returns
    -------
    nnz : int, float, ndarray of shape (n_samples,) or ndarray of shape (n_features,)
        Number of non-zero values in the array along a given axis. Otherwise,
        the total number of non-zero values in the array is returned.
    """
    if axis == -1:
        axis = 1
    elif axis == -2:
        axis = 0
    elif X.format != "csr":
        raise TypeError("Expected CSR sparse format, got {0}".format(X.format))

    # We rely here on the fact that np.diff(Y.indptr) for a CSR
    # will return the number of nonzero entries in each row.
    # A bincount over Y.indices will return the number of nonzeros
    # in each column. See ``csr_matrix.getnnz`` in scipy >= 0.14.
    if axis is None:
        if sample_weight is None:
            return X.nnz
        else:
            return np.dot(np.diff(X.indptr), sample_weight)
    elif axis == 1:
        out = np.diff(X.indptr)
        if sample_weight is None:
            # astype here is for consistency with axis=0 dtype
            return out.astype("intp")
        return out * sample_weight
    elif axis == 0:
        if sample_weight is None:
            return np.bincount(X.indices, minlength=X.shape[1])
        else:
            weights = np.repeat(sample_weight, np.diff(X.indptr))
            return np.bincount(X.indices, minlength=X.shape[1], weights=weights)
    else:
        raise ValueError("Unsupported axis: {0}".format(axis))