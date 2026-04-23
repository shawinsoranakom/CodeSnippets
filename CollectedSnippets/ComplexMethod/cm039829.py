def as_float_array(X, *, copy=True, ensure_all_finite=True):
    """Convert an array-like to an array of floats.

    The new dtype will be np.float32 or np.float64, depending on the original
    type. The function can create a copy or modify the argument depending
    on the argument copy.

    Parameters
    ----------
    X : {array-like, sparse matrix}
        The input data.

    copy : bool, default=True
        If True, a copy of X will be created. If False, a copy may still be
        returned if X's dtype is not a floating point type.

    ensure_all_finite : bool or 'allow-nan', default=True
        Whether to raise an error on np.inf, np.nan, pd.NA in X. The
        possibilities are:

        - True: Force all values of X to be finite.
        - False: accepts np.inf, np.nan, pd.NA in X.
        - 'allow-nan': accepts only np.nan and pd.NA values in X. Values cannot
          be infinite.

        .. versionadded:: 1.6
           `force_all_finite` was renamed to `ensure_all_finite`.

    Returns
    -------
    XT : {ndarray, sparse matrix}
        An array of type float.

    Examples
    --------
    >>> from sklearn.utils import as_float_array
    >>> import numpy as np
    >>> array = np.array([0, 0, 1, 2, 2], dtype=np.int64)
    >>> as_float_array(array)
    array([0., 0., 1., 2., 2.])
    """
    if isinstance(X, np.matrix) or (
        not isinstance(X, np.ndarray) and not sp.issparse(X)
    ):
        return check_array(
            X,
            accept_sparse=["csr", "csc", "coo"],
            dtype=np.float64,
            copy=copy,
            ensure_all_finite=ensure_all_finite,
            ensure_2d=False,
        )
    elif sp.issparse(X) and X.dtype in [np.float32, np.float64]:
        return X.copy() if copy else X
    elif X.dtype in [np.float32, np.float64]:  # is numpy array
        return X.copy("F" if X.flags["F_CONTIGUOUS"] else "C") if copy else X
    else:
        if X.dtype.kind in "uib" and X.dtype.itemsize <= 4:
            return_dtype = np.float32
        else:
            return_dtype = np.float64
        return X.astype(return_dtype)