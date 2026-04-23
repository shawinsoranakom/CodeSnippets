def _pyarrow_indexing(X, key, key_dtype, axis):
    """Index a pyarrow data."""
    scalar_key = np.isscalar(key)
    if isinstance(key, slice):
        if isinstance(key.stop, str):
            start = X.column_names.index(key.start)
            stop = X.column_names.index(key.stop) + 1
        else:
            start = 0 if not key.start else key.start
            stop = key.stop
        step = 1 if not key.step else key.step
        key = list(range(start, stop, step))

    if axis == 1:
        # Here we are certain that X is a pyarrow Table or RecordBatch.
        if key_dtype == "int" and not isinstance(key, list):
            # pyarrow's X.select behavior is more consistent with integer lists.
            key = np.asarray(key).tolist()
        if key_dtype == "bool":
            key = np.asarray(key).nonzero()[0].tolist()

        if scalar_key:
            return X.column(key)

        return X.select(key)

    # axis == 0 from here on
    if scalar_key:
        if hasattr(X, "shape"):
            # X is a Table or RecordBatch
            key = [key]
        else:
            return X[key].as_py()
    elif not isinstance(key, list):
        key = np.asarray(key)

    if key_dtype == "bool":
        # TODO(pyarrow): remove version checking and following if-branch when
        # pyarrow==17.0.0 is the minimal version, see pyarrow issue
        # https://github.com/apache/arrow/issues/42013 for more info
        if PYARROW_VERSION_BELOW_17:
            import pyarrow

            if not isinstance(key, pyarrow.BooleanArray):
                key = pyarrow.array(key, type=pyarrow.bool_())

        X_indexed = X.filter(key)

    else:
        X_indexed = X.take(key)

    if scalar_key and len(getattr(X, "shape", [0])) == 2:
        # X_indexed is a dataframe-like with a single row; we return a Series to be
        # consistent with pandas
        pa = sys.modules["pyarrow"]
        return pa.array(X_indexed.to_pylist()[0].values())
    return X_indexed