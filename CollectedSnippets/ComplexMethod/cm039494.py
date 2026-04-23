def check_pairwise_arrays(
    X,
    Y,
    *,
    precomputed=False,
    dtype="infer_float",
    accept_sparse="csr",
    ensure_all_finite=True,
    ensure_2d=True,
    copy=False,
):
    """Set X and Y appropriately and checks inputs.

    If Y is None, it is set as a pointer to X (i.e. not a copy).
    If Y is given, this does not happen.
    All distance metrics should use this function first to assert that the
    given parameters are correct and safe to use.

    Specifically, this function first ensures that both X and Y are arrays,
    then checks that they are at least two dimensional while ensuring that
    their elements are floats (or dtype if provided). Finally, the function
    checks that the size of the second dimension of the two arrays is equal, or
    the equivalent check for a precomputed distance matrix.

    Parameters
    ----------
    X : {array-like, sparse matrix} of shape (n_samples_X, n_features)

    Y : {array-like, sparse matrix} of shape (n_samples_Y, n_features)

    precomputed : bool, default=False
        True if X is to be treated as precomputed distances to the samples in
        Y.

    dtype : str, type, list of type or None default="infer_float"
        Data type required for X and Y. If "infer_float", the dtype will be an
        appropriate float type selected by _return_float_dtype. If None, the
        dtype of the input is preserved.

        .. versionadded:: 0.18

    accept_sparse : str, bool or list/tuple of str, default='csr'
        String[s] representing allowed sparse matrix formats, such as 'csc',
        'csr', etc. If the input is sparse but not in the allowed format,
        it will be converted to the first listed format. True allows the input
        to be any format. False means that a sparse matrix input will
        raise an error.

    ensure_all_finite : bool or 'allow-nan', default=True
        Whether to raise an error on np.inf, np.nan, pd.NA in array. The
        possibilities are:

        - True: Force all values of array to be finite.
        - False: accepts np.inf, np.nan, pd.NA in array.
        - 'allow-nan': accepts only np.nan and pd.NA values in array. Values
          cannot be infinite.

        .. versionadded:: 1.6
           `force_all_finite` was renamed to `ensure_all_finite`.

    ensure_2d : bool, default=True
        Whether to raise an error when the input arrays are not 2-dimensional. Setting
        this to `False` is necessary when using a custom metric with certain
        non-numerical inputs (e.g. a list of strings).

        .. versionadded:: 1.5

    copy : bool, default=False
        Whether a forced copy will be triggered. If copy=False, a copy might
        be triggered by a conversion.

        .. versionadded:: 0.22

    Returns
    -------
    safe_X : {array-like, sparse matrix} of shape (n_samples_X, n_features)
        An array equal to X, guaranteed to be a numpy array.

    safe_Y : {array-like, sparse matrix} of shape (n_samples_Y, n_features)
        An array equal to Y if Y was not None, guaranteed to be a numpy array.
        If Y was None, safe_Y will be a pointer to X.
    """
    xp, _ = get_namespace(X, Y)
    X, Y, dtype_float = _find_floating_dtype_allow_sparse(X, Y, xp=xp)

    estimator = "check_pairwise_arrays"
    if dtype == "infer_float":
        dtype = dtype_float

    if Y is X or Y is None:
        X = Y = check_array(
            X,
            accept_sparse=accept_sparse,
            dtype=dtype,
            copy=copy,
            ensure_all_finite=ensure_all_finite,
            estimator=estimator,
            ensure_2d=ensure_2d,
        )
    else:
        X = check_array(
            X,
            accept_sparse=accept_sparse,
            dtype=dtype,
            copy=copy,
            ensure_all_finite=ensure_all_finite,
            estimator=estimator,
            ensure_2d=ensure_2d,
        )
        Y = check_array(
            Y,
            accept_sparse=accept_sparse,
            dtype=dtype,
            copy=copy,
            ensure_all_finite=ensure_all_finite,
            estimator=estimator,
            ensure_2d=ensure_2d,
        )

    if precomputed:
        if X.shape[1] != Y.shape[0]:
            raise ValueError(
                "Precomputed metric requires shape "
                "(n_queries, n_indexed). Got (%d, %d) "
                "for %d indexed." % (X.shape[0], X.shape[1], Y.shape[0])
            )
    elif ensure_2d and X.shape[1] != Y.shape[1]:
        # Only check the number of features if 2d arrays are enforced. Otherwise,
        # validation is left to the user for custom metrics.
        raise ValueError(
            "Incompatible dimension for X and Y matrices: "
            "X.shape[1] == %d while Y.shape[1] == %d" % (X.shape[1], Y.shape[1])
        )

    return X, Y