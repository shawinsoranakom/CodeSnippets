def _is_date_column(df: pd.DataFrame, name: Hashable) -> bool:
    """True if the column with the given name stores datetime.date values.

    This function just checks the first value in the given column, so
    it's meaningful only for columns whose values all share the same type.

    Parameters
    ----------
    df : pd.DataFrame
    name : hashable
        The column name

    Returns
    -------
    bool

    """
    column = df[name]
    if column.size == 0:
        return False
    return isinstance(column[0], date)