def calculate_fib_levels(
    data: "DataFrame",
    close_col: str,
    limit: int = 120,
    start_date: Any | None = None,
    end_date: Any | None = None,
) -> tuple["DataFrame", "Timestamp", "Timestamp", float, float, str]:
    """Calculate Fibonacci levels.

    Parameters
    ----------
    data : DataFrame
        Dataframe of prices
    close_col : str
        Column name of close prices
    limit : int
        Days to look back for retracement
    start_date : Any
        Custom start date for retracement
    end_date : Any
        Custom end date for retracement

    Returns
    -------
    df : DataFrame
        Dataframe of fib levels
    min_date: Timestamp
        Date of min point
    max_date: Timestamp:
        Date of max point
    min_pr: float
        Price at min point
    max_pr: float
        Price at max point
    """
    # pylint: disable=import-outside-toplevel
    from pandas import DataFrame

    if close_col not in data.columns:
        raise ValueError(f"Column {close_col} not in data")

    if start_date and end_date:
        if start_date not in data.index:
            date0 = data.index[data.index.get_indexer([end_date], method="nearest")[0]]
            warn(f"Start date not in data.  Using nearest: {date0}")
        else:
            date0 = start_date
        if end_date not in data.index:
            date1 = data.index[data.index.get_indexer([end_date], method="nearest")[0]]
            warn(f"End date not in data.  Using nearest: {date1}")
        else:
            date1 = end_date

        data0 = data.loc[date0, close_col]
        data1 = data.loc[date1, close_col]

        min_pr = min(data0, data1)
        max_pr = max(data0, data1)

        if min_pr == data0:
            min_date = date0
            max_date = date1
        else:
            min_date = date1
            max_date = date0
    else:
        data_to_use = data.iloc[-limit:, :][close_col]

        min_pr = data_to_use.min()
        min_date = data_to_use.idxmin()
        max_pr = data_to_use.max()
        max_date = data_to_use.idxmax()

    fib_levels = [0, 0.235, 0.382, 0.5, 0.618, 0.65, 1]

    lvl_text: str = "left" if min_date < max_date else "right"
    if min_date > max_date:
        min_date, max_date = max_date, min_date
        min_pr, max_pr = max_pr, min_pr

    price_dif = max_pr - min_pr

    levels = [
        round(max_pr - price_dif * f_lev, (2 if f_lev > 1 else 4))
        for f_lev in fib_levels
    ]

    df = DataFrame()
    df["Level"] = fib_levels
    df["Level"] = df["Level"].apply(lambda x: str(x * 100) + "%")
    df["Price"] = levels

    return df, min_date, max_date, min_pr, max_pr, lvl_text