def _safe_indexing(X, indices, *, axis=0):
    """Return rows, items or columns of X using indices.

    .. warning::

        This utility is documented, but **private**. This means that
        backward compatibility might be broken without any deprecation
        cycle.

    Parameters
    ----------
    X : array-like, sparse-matrix, list, pandas.DataFrame, pandas.Series
        Data from which to sample rows, items or columns. `list` are only
        supported when `axis=0`.
    indices : bool, int, str, slice, array-like
        - If `axis=0`, boolean and integer array-like, integer slice,
          and scalar integer are supported.
        - If `axis=1`:
            - to select a single column, `indices` can be of `int` type for
              all `X` types and `str` only for dataframe. The selected subset
              will be 1D, unless `X` is a sparse matrix in which case it will
              be 2D.
            - to select multiples columns, `indices` can be one of the
              following: `list`, `array`, `slice`. The type used in
              these containers can be one of the following: `int`, 'bool' and
              `str`. However, `str` is only supported when `X` is a dataframe.
              The selected subset will be 2D.
    axis : int, default=0
        The axis along which `X` will be subsampled. `axis=0` will select
        rows while `axis=1` will select columns.

    Returns
    -------
    subset
        Subset of X on axis 0 or 1.

    Notes
    -----
    CSR, CSC, and LIL sparse matrices are supported. COO sparse matrices are
    not supported.

    Examples
    --------
    >>> import numpy as np
    >>> from sklearn.utils import _safe_indexing
    >>> data = np.array([[1, 2], [3, 4], [5, 6]])
    >>> _safe_indexing(data, 0, axis=0)  # select the first row
    array([1, 2])
    >>> _safe_indexing(data, 0, axis=1)  # select the first column
    array([1, 3, 5])
    """
    if indices is None:
        return X

    if axis not in (0, 1):
        raise ValueError(
            "'axis' should be either 0 (to index rows) or 1 (to index "
            " column). Got {} instead.".format(axis)
        )

    indices_dtype = _determine_key_type(indices)

    if axis == 0 and indices_dtype == "str":
        raise ValueError(
            f"String indexing (indices={indices}) is not supported with 'axis=0'. "
            "Did you mean to use axis=1 for column selection?"
        )

    if axis == 1 and isinstance(X, list):
        raise ValueError("axis=1 is not supported for lists")

    if axis == 1 and (ndim := len(getattr(X, "shape", [0]))) != 2:
        raise ValueError(
            "'X' should be a 2D NumPy array, 2D sparse matrix or "
            "dataframe when indexing the columns (i.e. 'axis=1'). "
            f"Got {type(X)} instead with {ndim} dimension(s)."
        )

    if (
        axis == 1
        and indices_dtype == "str"
        and not (is_pandas_df(X) or _use_interchange_protocol(X))
    ):
        raise ValueError(
            "Specifying the columns using strings is only supported for dataframes."
        )

    if hasattr(X, "iloc"):
        # TODO: we should probably use is_pandas_df_or_series(X) instead but:
        # 1) Currently, it (probably) works for dataframes compliant to pandas' API.
        # 2) Updating would require updating some tests such as
        #    test_train_test_split_mock_pandas.
        return _pandas_indexing(X, indices, indices_dtype, axis=axis)
    elif is_polars_df_or_series(X):
        return _polars_indexing(X, indices, indices_dtype, axis=axis)
    elif is_pyarrow_data(X):
        return _pyarrow_indexing(X, indices, indices_dtype, axis=axis)
    elif _use_interchange_protocol(X):  # pragma: no cover
        # Once the dataframe X is converted into its dataframe interchange protocol
        # version by calling X.__dataframe__(), it becomes very hard to turn it back
        # into its original type, e.g., a pyarrow.Table, see
        # https://github.com/data-apis/dataframe-api/issues/85.
        raise warnings.warn(
            message="A data object with support for the dataframe interchange protocol"
            "was passed, but scikit-learn does currently not know how to handle this "
            "kind of data. Some array/list indexing will be tried.",
            category=UserWarning,
        )

    if hasattr(X, "shape"):
        return _array_indexing(X, indices, indices_dtype, axis=axis)
    else:
        return _list_indexing(X, indices, indices_dtype)