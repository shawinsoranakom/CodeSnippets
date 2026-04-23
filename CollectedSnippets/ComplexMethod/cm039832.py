def _ensure_sparse_format(
    sparse_container,
    accept_sparse,
    dtype,
    copy,
    ensure_all_finite,
    accept_large_sparse,
    estimator_name=None,
    input_name="",
):
    """Convert a sparse container to a given format.

    Checks the sparse format of `sparse_container` and converts if necessary.

    Parameters
    ----------
    sparse_container : sparse matrix or array
        Input to validate and convert.

    accept_sparse : str, bool or list/tuple of str
        String[s] representing allowed sparse matrix formats ('csc',
        'csr', 'coo', 'dok', 'bsr', 'lil', 'dia'). If the input is sparse but
        not in the allowed format, it will be converted to the first listed
        format. True allows the input to be any format. False means
        that a sparse matrix input will raise an error.

    dtype : str, type or None
        Data type of result. If None, the dtype of the input is preserved.

    copy : bool
        Whether a forced copy will be triggered. If copy=False, a copy might
        be triggered by a conversion.

    ensure_all_finite : bool or 'allow-nan'
        Whether to raise an error on np.inf, np.nan, pd.NA in X. The
        possibilities are:

        - True: Force all values of X to be finite.
        - False: accepts np.inf, np.nan, pd.NA in X.
        - 'allow-nan': accepts only np.nan and pd.NA values in X. Values cannot
          be infinite.

        .. versionadded:: 0.20
           ``ensure_all_finite`` accepts the string ``'allow-nan'``.

        .. versionchanged:: 0.23
           Accepts `pd.NA` and converts it into `np.nan`

    accept_large_sparse : bool
        If a CSR, CSC, COO or BSR sparse matrix is supplied and accepted by
        accept_sparse, accept_large_sparse will cause it to be accepted only
        if its indices are stored with a 32-bit dtype.

    estimator_name : str, default=None
        The estimator name, used to construct the error message.

    input_name : str, default=""
        The data name used to construct the error message. In particular
        if `input_name` is "X" and the data has NaN values and
        allow_nan is False, the error message will link to the imputer
        documentation.

    Returns
    -------
    sparse_container_converted : sparse matrix or array
        Sparse container (matrix/array) that is ensured to have an allowed type.
    """
    if dtype is None:
        dtype = sparse_container.dtype

    changed_format = False
    sparse_container_type_name = type(sparse_container).__name__

    if isinstance(accept_sparse, str):
        accept_sparse = [accept_sparse]

    # Indices dtype validation
    _check_large_sparse(sparse_container, accept_large_sparse)

    if accept_sparse is False:
        padded_input = " for " + input_name if input_name else ""
        raise TypeError(
            f"Sparse data was passed{padded_input}, but dense data is required. "
            "Use '.toarray()' to convert to a dense numpy array."
        )
    elif isinstance(accept_sparse, (list, tuple)):
        if len(accept_sparse) == 0:
            raise ValueError(
                "When providing 'accept_sparse' as a tuple or list, it must contain at "
                "least one string value."
            )
        # ensure correct sparse format
        if sparse_container.format not in accept_sparse:
            # create new with correct sparse
            sparse_container = sparse_container.asformat(accept_sparse[0])
            changed_format = True
    elif accept_sparse is not True:
        # any other type
        raise ValueError(
            "Parameter 'accept_sparse' should be a string, boolean or list of strings."
            f" You provided 'accept_sparse={accept_sparse}'."
        )

    if dtype != sparse_container.dtype:
        # convert dtype
        sparse_container = sparse_container.astype(dtype)
    elif copy and not changed_format:
        # force copy
        sparse_container = sparse_container.copy()

    if ensure_all_finite:
        if not hasattr(sparse_container, "data"):
            warnings.warn(
                f"Can't check {sparse_container.format} sparse matrix for nan or inf.",
                stacklevel=2,
            )
        else:
            _assert_all_finite(
                sparse_container.data,
                allow_nan=ensure_all_finite == "allow-nan",
                estimator_name=estimator_name,
                input_name=input_name,
            )

    # TODO: Remove when the minimum version of SciPy supported is 1.12
    # With SciPy sparse arrays, conversion from DIA format to COO, CSR, or BSR
    # triggers the use of `np.int64` indices even if the data is such that it could
    # be more efficiently represented with `np.int32` indices.
    # https://github.com/scipy/scipy/issues/19245 Since not all scikit-learn
    # algorithms support large indices, the following code downcasts to `np.int32`
    # indices when it's safe to do so.
    if changed_format:
        # accept_sparse is specified to a specific format and a conversion occurred
        requested_sparse_format = accept_sparse[0]
        _preserve_dia_indices_dtype(
            sparse_container, sparse_container_type_name, requested_sparse_format
        )

    return sparse_container