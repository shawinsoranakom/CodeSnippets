def normalize(X, norm="l2", *, axis=1, copy=True, return_norm=False):
    """Scale input vectors individually to unit norm (vector length).

    Read more in the :ref:`User Guide <preprocessing_normalization>`.

    Parameters
    ----------
    X : {array-like, sparse matrix} of shape (n_samples, n_features)
        The data to normalize, element by element.
        scipy.sparse matrices should be in CSR format to avoid an
        un-necessary copy.

    norm : {'l1', 'l2', 'max'}, default='l2'
        The norm to use to normalize each non zero sample (or each non-zero
        feature if axis is 0).

    axis : {0, 1}, default=1
        Define axis used to normalize the data along. If 1, independently
        normalize each sample, otherwise (if 0) normalize each feature.

    copy : bool, default=True
        If False, try to avoid a copy and normalize in place.
        This is not guaranteed to always work in place; e.g. if the data is
        a numpy array with an int dtype, a copy will be returned even with
        copy=False.

    return_norm : bool, default=False
        Whether to return the computed norms.

    Returns
    -------
    X : {ndarray, sparse matrix} of shape (n_samples, n_features)
        Normalized input X.

    norms : ndarray of shape (n_samples, ) if axis=1 else (n_features, )
        An array of norms along given axis for X.
        When X is sparse, a NotImplementedError will be raised
        for norm 'l1' or 'l2'.

    See Also
    --------
    Normalizer : Performs normalization using the Transformer API
        (e.g. as part of a preprocessing :class:`~sklearn.pipeline.Pipeline`).

    Notes
    -----
    For a comparison of the different scalers, transformers, and normalizers,
    see: :ref:`sphx_glr_auto_examples_preprocessing_plot_all_scaling.py`.

    Examples
    --------
    >>> from sklearn.preprocessing import normalize
    >>> X = [[-2, 1, 2], [-1, 0, 1]]
    >>> normalize(X, norm="l1")  # L1 normalization each row independently
    array([[-0.4,  0.2,  0.4],
           [-0.5,  0. ,  0.5]])
    >>> normalize(X, norm="l2")  # L2 normalization each row independently
    array([[-0.67, 0.33, 0.67],
           [-0.71, 0.  , 0.71]])
    """
    if axis == 0:
        sparse_format = "csc"
    else:  # axis == 1:
        sparse_format = "csr"

    xp, _ = get_namespace(X)

    X = check_array(
        X,
        accept_sparse=sparse_format,
        copy=copy,
        estimator="the normalize function",
        dtype=_array_api.supported_float_dtypes(xp),
        force_writeable=True,
    )
    if axis == 0:
        X = X.T

    if sparse.issparse(X):
        if return_norm and norm in ("l1", "l2"):
            raise NotImplementedError(
                "return_norm=True is not implemented "
                "for sparse matrices with norm 'l1' "
                "or norm 'l2'"
            )
        if norm == "l1":
            inplace_csr_row_normalize_l1(X)
        elif norm == "l2":
            inplace_csr_row_normalize_l2(X)
        elif norm == "max":
            mins, maxes = min_max_axis(X, 1)
            norms = np.maximum(abs(mins), maxes)
            norms_elementwise = norms.repeat(np.diff(X.indptr))
            mask = norms_elementwise != 0
            X.data[mask] /= norms_elementwise[mask]
    else:
        if norm == "l1":
            norms = xp.sum(xp.abs(X), axis=1)
        elif norm == "l2":
            norms = row_norms(X)
        elif norm == "max":
            norms = xp.max(xp.abs(X), axis=1)
        norms = _handle_zeros_in_scale(norms, copy=False)
        X /= norms[:, None]

    if axis == 0:
        X = X.T

    if return_norm:
        return X, norms
    else:
        return X