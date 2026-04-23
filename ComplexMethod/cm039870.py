def _get_column_indices(X, key):
    """Get feature column indices for input data X and key.

    For accepted values of `key`, see the docstring of
    :func:`_safe_indexing`.
    """
    key_dtype = _determine_key_type(key)
    if _use_interchange_protocol(X):
        return _get_column_indices_interchange(X.__dataframe__(), key, key_dtype)

    n_columns = X.shape[1]
    if isinstance(key, (list, tuple)) and not key:
        # we get an empty list
        return []
    elif key_dtype in ("bool", "int"):
        return _get_column_indices_for_bool_or_int(key, n_columns)
    else:
        try:
            all_columns = X.columns
        except AttributeError:
            raise ValueError(
                "Specifying the columns using strings is only supported for dataframes."
            )
        if isinstance(key, str):
            columns = [key]
        elif isinstance(key, slice):
            start, stop = key.start, key.stop
            if start is not None:
                start = all_columns.get_loc(start)
            if stop is not None:
                # pandas indexing with strings is endpoint included
                stop = all_columns.get_loc(stop) + 1
            else:
                stop = n_columns + 1
            return list(islice(range(n_columns), start, stop))
        else:
            columns = list(key)

        try:
            column_indices = []
            for col in columns:
                col_idx = all_columns.get_loc(col)
                if not isinstance(col_idx, numbers.Integral):
                    raise ValueError(
                        f"Selected columns, {columns}, are not unique in dataframe"
                    )
                column_indices.append(col_idx)

        except KeyError as e:
            raise ValueError("A given column is not a column of the dataframe") from e

        return column_indices