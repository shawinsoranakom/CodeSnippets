def yf_download(  # pylint: disable=too-many-positional-arguments
    symbol: str,
    start_date: Union[str, "date"] | None = None,
    end_date: Union[str, "date"] | None = None,
    interval: INTERVALS = "1d",
    period: PERIODS | None = None,
    prepost: bool = False,
    actions: bool = False,
    progress: bool = False,
    ignore_tz: bool = True,
    keepna: bool = False,
    repair: bool = False,
    rounding: bool = False,
    group_by: Literal["ticker", "column"] = "ticker",
    adjusted: bool = False,
    **kwargs: Any,
) -> "DataFrame":
    """Get yFinance OHLC data for any ticker and interval available."""
    # pylint: disable=import-outside-toplevel
    from datetime import datetime, timedelta  # noqa
    from pandas import DataFrame, concat, to_datetime
    import yfinance as yf

    symbol = symbol.upper()
    _start_date = start_date
    intraday = False
    if interval in ["60m", "1h"]:
        period = "2y" if period in ["5y", "10y", "max"] else period
        _start_date = None
        intraday = True

    if interval in ["2m", "5m", "15m", "30m", "90m"]:
        _start_date = (datetime.now().date() - timedelta(days=58)).strftime("%Y-%m-%d")
        intraday = True

    if interval == "1m":
        period = "5d"
        _start_date = None
        intraday = True

    if adjusted is False:
        kwargs.update(dict(auto_adjust=False, back_adjust=False, period=period))

    # Note: Proxy support via kwargs["proxy"] is preserved if provided.
    # yfinance>=0.2.66 manages its own curl_cffi sessions internally.
    # If a session was passed in kwargs, extract proxy info before removing it.
    session = kwargs.pop("session", None)
    if session and hasattr(session, "proxies") and session.proxies:
        kwargs["proxy"] = session.proxies

    try:
        data = yf.download(
            tickers=symbol,
            start=_start_date,
            end=None,
            interval=interval,
            prepost=prepost,
            actions=actions,
            progress=progress,
            ignore_tz=ignore_tz,
            keepna=keepna,
            repair=repair,
            rounding=rounding,
            group_by=group_by,
            threads=False,
            **kwargs,
        )
        if hasattr(data.index, "tz") and data.index.tz is not None:  # type: ignore
            data = data.tz_convert(None)  # type: ignore

    except ValueError as exc:
        raise EmptyDataError() from exc

    tickers = symbol.split(",")
    if len(tickers) == 1:
        data = data.get(symbol, DataFrame())  # type: ignore
    elif len(tickers) > 1:
        _data = DataFrame()
        for ticker in tickers:
            temp = data[ticker].copy().dropna(how="all")  # type: ignore
            if len(temp) > 0:
                temp["symbol"] = ticker
                temp = temp.reset_index().rename(
                    columns={"Date": "date", "Datetime": "date", "index": "date"}
                )
                _data = concat([_data, temp])
        if not _data.empty:
            index_keys = ["date", "symbol"] if "symbol" in _data.columns else "date"
            _data = _data.set_index(index_keys).sort_index()
            data = _data

    if data.empty:  # type: ignore
        raise EmptyDataError()

    data = data.reset_index()  # type: ignore
    data = data.rename(columns={"Date": "date", "Datetime": "date"})
    data["date"] = data["date"].apply(to_datetime)
    data = data[data["Open"] > 0]

    if start_date is not None:
        data = data[data["date"] >= to_datetime(start_date)]  # type: ignore
    if (
        end_date is not None and start_date is not None and to_datetime(end_date) > to_datetime(start_date)  # type: ignore
    ):
        data = data[
            data["date"] <= (to_datetime(end_date) + timedelta(days=1 if intraday is True else 0))  # type: ignore
        ]
    if intraday is True:
        data["date"] = data["date"].dt.strftime("%Y-%m-%d %H:%M:%S")  # type: ignore
    else:
        data["date"] = data["date"].dt.strftime("%Y-%m-%d")  # type: ignore
    if adjusted is False:
        data = data.drop(columns=["Adj Close"])  # type: ignore
    data.columns = data.columns.str.lower().str.replace(" ", "_").to_list()  # type: ignore

    # Remove columns with no information.
    for col in ["dividends", "capital_gains", "stock_splits"]:
        if col in data.columns and data[col].sum() == 0:
            data = data.drop(columns=[col])

    return data