def _polars_indexing(X, key, key_dtype, axis):
    """Index a polars dataframe or series."""
    # Polars behavior is more consistent with lists
    if isinstance(key, np.ndarray):
        # Convert each element of the array to a Python scalar
        key = key.tolist()
    elif not (np.isscalar(key) or isinstance(key, slice)):
        key = list(key)

    if axis == 1:
        # Here we are certain to have a polars DataFrame; which can be indexed with
        # integer and string scalar, and list of integer, string and boolean
        return X[:, key]

    if key_dtype == "bool":
        # Boolean mask can be indexed in the same way for Series and DataFrame (axis=0)
        return X.filter(key)

    # Integer scalar and list of integer can be indexed in the same way for Series and
    # DataFrame (axis=0)
    X_indexed = X[key]
    if np.isscalar(key) and len(X.shape) == 2:
        # `X_indexed` is a DataFrame with a single row; we return a Series to be
        # consistent with pandas
        pl = sys.modules["polars"]
        return pl.Series(X_indexed.row(0))
    return X_indexed