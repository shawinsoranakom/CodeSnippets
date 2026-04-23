def _convert_container(
    container,
    constructor_name,
    columns_name=None,
    dtype=None,
    minversion=None,
    categorical_feature_names=None,
):
    """Convert a given container to a specific array-like with a dtype.

    Parameters
    ----------
    container : array-like
        The container to convert.
    constructor_name : {"list", "tuple", "array", "sparse", "dataframe", \
            "pandas", "series", "index", "slice", "sparse_csr", "sparse_csc", \
            "sparse_csr_array", "sparse_csc_array", "pyarrow", "polars", \
            "polars_series"}
        The type of the returned container.
    columns_name : index or array-like, default=None
        For pandas/polars container supporting `columns_names`, it will affect
        specific names.
    dtype : dtype, default=None
        Force the dtype of the container. Does not apply to `"slice"`
        container.
    minversion : str, default=None
        Minimum version for package to install.
    categorical_feature_names : list of str, default=None
        List of column names to cast to categorical dtype.

    Returns
    -------
    converted_container
    """
    if constructor_name == "list":
        if dtype is None:
            return list(container)
        else:
            return np.asarray(container, dtype=dtype).tolist()
    elif constructor_name == "tuple":
        if dtype is None:
            return tuple(container)
        else:
            return tuple(np.asarray(container, dtype=dtype).tolist())
    elif constructor_name == "array":
        return np.asarray(container, dtype=dtype)
    elif constructor_name in ("pandas", "dataframe"):
        pd = pytest.importorskip("pandas", minversion=minversion)
        result = pd.DataFrame(container, columns=columns_name, dtype=dtype, copy=False)
        if categorical_feature_names is not None:
            for col_name in categorical_feature_names:
                result[col_name] = result[col_name].astype("category")
        return result
    elif constructor_name == "pyarrow":
        pa = pytest.importorskip("pyarrow", minversion=minversion)
        array = np.asarray(container)
        array = array[:, None] if array.ndim == 1 else array
        if columns_name is None:
            columns_name = [f"col{i}" for i in range(array.shape[1])]
        data = {name: array[:, i] for i, name in enumerate(columns_name)}
        result = pa.Table.from_pydict(data)
        if categorical_feature_names is not None:
            for col_idx, col_name in enumerate(result.column_names):
                if col_name in categorical_feature_names:
                    result = result.set_column(
                        col_idx, col_name, result.column(col_name).dictionary_encode()
                    )
        return result
    elif constructor_name == "polars":
        pl = pytest.importorskip("polars", minversion=minversion)
        result = pl.DataFrame(container, schema=columns_name, orient="row")
        if categorical_feature_names is not None:
            for col_name in categorical_feature_names:
                result = result.with_columns(pl.col(col_name).cast(pl.Categorical))
        return result
    elif constructor_name == "series":
        pd = pytest.importorskip("pandas", minversion=minversion)
        return pd.Series(container, dtype=dtype)
    elif constructor_name == "pyarrow_array":
        pa = pytest.importorskip("pyarrow", minversion=minversion)
        return pa.array(container)
    elif constructor_name == "polars_series":
        pl = pytest.importorskip("polars", minversion=minversion)
        return pl.Series(values=container)
    elif constructor_name == "index":
        pd = pytest.importorskip("pandas", minversion=minversion)
        return pd.Index(container, dtype=dtype)
    elif constructor_name == "slice":
        return slice(container[0], container[1])
    elif "sparse" in constructor_name:
        if not sp.sparse.issparse(container):
            # For scipy >= 1.13, sparse array constructed from 1d array may be
            # 1d or raise an exception. To avoid this, we make sure that the
            # input container is 2d. For more details, see
            # https://github.com/scipy/scipy/pull/18530#issuecomment-1878005149
            container = np.atleast_2d(container)

        if constructor_name in ("sparse", "sparse_csr"):
            # sparse and sparse_csr are equivalent for legacy reasons
            return sp.sparse.csr_matrix(container, dtype=dtype)
        elif constructor_name == "sparse_csr_array":
            return sp.sparse.csr_array(container, dtype=dtype)
        elif constructor_name == "sparse_csc":
            return sp.sparse.csc_matrix(container, dtype=dtype)
        elif constructor_name == "sparse_csc_array":
            return sp.sparse.csc_array(container, dtype=dtype)