async def get_settlement_prices(
    settlement_date: dateType | None = None,
    options: bool = False,
    archives: bool = False,
    final_settlement: bool = False,
    **kwargs,
) -> "DataFrame":
    """Get the settlement prices of CBOE futures.

    Parameters
    ----------
    settlement_date: Optional[date]
        The settlement date. Only valid for active contracts. [YYYY-MM-DD]
    options: bool
        If true, returns options on futures.
    archives: bool
        Settlement price archives for select years and products.  Overridden by other parameters.
    final_settlement: bool
        Final settlement prices for expired contracts.  Overrides archives.

    Returns
    -------
    DataFrame
        Pandas DataFrame with results.
    """
    # pylint: disable=import-outside-toplevel
    from io import StringIO  # noqa
    from pandas import DataFrame, read_csv  # noqa

    url = ""
    if settlement_date is not None:
        url = (
            "https://www.cboe.com/us/futures/market_statistics"
            + f"/settlement/csv?dt={settlement_date}"
        )
        if options is True:
            url = (
                "https://www.cboe.com/us/futures/market_statistics/"
                + f"settlement/csv?options=t&dt={settlement_date}"
            )
    if settlement_date is None:
        url = "https://www.cboe.com/us/futures/market_statistics/settlement/csv"
        if options is True:
            url = "https://www.cboe.com/us/futures/market_statistics/settlement/csv?options=t"

    if final_settlement is True:
        url = "https://www.cboe.com/us/futures/market_statistics/final_settlement_prices/csv/"

    if archives is True:
        url = (
            "https://cdn.cboe.com/resources/futures/archive"
            + "/volume-and-price/CFE_FinalSettlement_Archive.csv"
        )

    response = await get_cboe_data(url, use_cache=False, **kwargs)

    data = read_csv(StringIO(response), index_col=None, parse_dates=True)

    if data.empty:
        return DataFrame()

    data.columns = [to_snake_case(c) for c in data.columns]
    data = data.rename(columns={"expiration_date": "expiration"})

    if len(data) > 0:
        return data

    return DataFrame()