def safe_sparse_dot(a, b, *, dense_output=False):
    """Dot product that handle the sparse matrix case correctly.

    Parameters
    ----------
    a : {ndarray, sparse matrix}
    b : {ndarray, sparse matrix}
    dense_output : bool, default=False
        When False, ``a`` and ``b`` both being sparse will yield sparse output.
        When True, output will always be a dense array.

    Returns
    -------
    dot_product : {ndarray, sparse matrix}
        Sparse if ``a`` and ``b`` are sparse and ``dense_output=False``.

    Examples
    --------
    >>> from scipy.sparse import csr_array
    >>> from sklearn.utils.extmath import safe_sparse_dot
    >>> X = csr_array([[1, 2], [3, 4], [5, 6]])
    >>> dot_product = safe_sparse_dot(X, X.T)
    >>> dot_product.toarray()
    array([[ 5, 11, 17],
           [11, 25, 39],
           [17, 39, 61]])
    """
    xp, _ = get_namespace(a, b)
    if a.ndim > 2 or b.ndim > 2:
        if sparse.issparse(a):
            # sparse is always 2D. Implies b is 3D+
            # [i, j] @ [k, ..., l, m, n] -> [i, k, ..., l, n]
            b_ = np.rollaxis(b, -2)
            b_2d = b_.reshape((b.shape[-2], -1))
            ret = a @ b_2d
            ret = ret.reshape(a.shape[0], *b_.shape[1:])
        elif sparse.issparse(b):
            # sparse is always 2D. Implies a is 3D+
            # [k, ..., l, m] @ [i, j] -> [k, ..., l, j]
            a_2d = a.reshape(-1, a.shape[-1])
            ret = a_2d @ b
            ret = ret.reshape(*a.shape[:-1], b.shape[1])
        else:
            # Alternative for `np.dot` when dealing with a or b having
            # more than 2 dimensions, that works with the array api.
            # If b is 1-dim then the last axis for b is taken otherwise
            # if b is >= 2-dim then the second to last axis is taken.
            b_axis = -1 if b.ndim == 1 else -2
            ret = xp.tensordot(a, b, axes=[-1, b_axis])
    elif (
        dense_output
        and a.ndim == 2
        and b.ndim == 2
        and a.dtype in (np.float32, np.float64)
        and b.dtype in (np.float32, np.float64)
        and (sparse.issparse(a) and a.format in ("csc", "csr"))
        and (sparse.issparse(b) and b.format in ("csc", "csr"))
    ):
        # Use dedicated fast method for dense_C = sparse_A @ sparse_B
        return sparse_matmul_to_dense(a, b)
    else:
        ret = a @ b

    if (
        sparse.issparse(a)
        and sparse.issparse(b)
        and dense_output
        and hasattr(ret, "toarray")
    ):
        return ret.toarray()
    return ret