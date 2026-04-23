async def get_vx_current(
    vx_type: Literal["am", "eod"] = "eod", use_cache: bool = True
) -> "DataFrame":
    """Get the current quotes for VX Futures.

    Parameters
    ----------
    vx_type : Literal["am", "eod"]
        The type of VX futures to get. Default is "eod".
            am: Mid-morning TWAP value
            eod: End-of-day value
    use_cache : bool
        Whether to use the cache. Default is True. Cache is only used for symbol mapping.

    Returns
    -------
    DataFrame
        DataFrame with the current VX futures data.
    """
    # pylint: disable=import-outside-toplevel
    from datetime import datetime  # noqa
    from openbb_core.app.model.abstract.error import OpenBBError
    from openbb_cboe.models.equity_quote import CboeEquityQuoteFetcher
    from pandas import DataFrame

    if vx_type not in ["am", "eod"]:
        raise OpenBBError("vx_type must be one of: 'am', 'eod'")

    current_symbols = list(get_vx_symbols().values())[:9]
    symbols = VX_AM_SYMBOLS if vx_type == "am" else current_symbols
    current_months = [VX_EOD_SYMBOL_TO_MONTH.get(d) for d in current_symbols]
    current_year = datetime.today().year
    data = await CboeEquityQuoteFetcher.fetch_data(
        {"symbol": ",".join(symbols), "use_cache": use_cache}, {}
    )
    df = DataFrame([d.model_dump() for d in data])  # type: ignore

    if vx_type == "am":
        df = df[["symbol", "last_price"]]
    elif vx_type == "eod":
        df = df.sort_values(by="last_timestamp", ascending=False)[
            ["symbol", "last_price"]
        ]
        df = df.set_index("symbol")
        df = df.filter(items=current_symbols, axis=0).reset_index()
        df = df.rename(columns={"index": "symbol"})

    expirations: list = []
    for month in current_months:
        new_year = month == 1
        current_year = (
            current_year + 1
            if new_year and datetime.today().month != 1
            else current_year
        )
        new_month = "0" + str(month) if month < 10 else str(month)  # type: ignore
        expirations.append(f"{current_year}-{new_month}")

    df.symbol = expirations
    df = df.rename(columns={"symbol": "expiration", "last_price": "price"}).dropna(
        how="any"
    )

    return df