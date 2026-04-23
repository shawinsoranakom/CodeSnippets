def _is_empty_column_selection(column):
    """
    Return True if the column selection is empty (empty list or all-False
    boolean array).

    """
    if (
        hasattr(column, "dtype")
        # Not necessarily a numpy dtype, can be a pandas dtype as well
        and isinstance(column.dtype, np.dtype)
        and np.issubdtype(column.dtype, np.bool_)
    ):
        return not column.any()
    elif hasattr(column, "__len__"):
        return len(column) == 0 or (
            all(isinstance(col, bool) for col in column) and not any(column)
        )
    else:
        return False