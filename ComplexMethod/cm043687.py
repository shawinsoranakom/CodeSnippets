async def download_eod_chains(
    symbol: str, date: dateType | None = None, use_cache: bool = False
) -> "DataFrame":
    """Download EOD chains data for a given symbol and date."""
    # pylint: disable=import-outside-toplevel
    from io import StringIO  # noqa
    import exchange_calendars as xcals  # noqa
    from pandas import DatetimeIndex, Timedelta, read_csv, to_datetime  # noqa
    from openbb_core.provider.utils.helpers import to_snake_case  # noqa

    symbol = symbol.upper()
    SYMBOLS = await get_all_options_tickers(use_cache=False)
    # Remove echange  identifiers from the symbol.
    symbol = symbol.upper().replace("-", ".").replace(".TO", "").replace(".TSX", "")

    # Underlying symbol may have a different ticker symbol than the ticker used to lookup options.
    if len(SYMBOLS[SYMBOLS["underlying_symbol"].str.contains(symbol)]) == 1:
        symbol = SYMBOLS[SYMBOLS["underlying_symbol"] == symbol].index.values[0]
    # Check if the symbol has options trading.
    if symbol not in SYMBOLS.index and not SYMBOLS.empty:
        raise OpenBBError(
            f"The symbol, {symbol}, is not a valid listing or does not trade options."
        )

    BASE_URL = "https://www.m-x.ca/en/trading/data/historical?symbol="

    cal = xcals.get_calendar("XTSE")

    def _is_session(dt: str) -> bool:
        """Check if date is a trading session.

        Workaround for exchange_calendars bug with Pandas 3 where
        is_session() fails due to ns/us unit mismatch in _date_oob.
        """
        return to_datetime(dt) in cal.sessions

    if date is None:
        EOD_URL = BASE_URL + f"{symbol}&dnld=1#quotes"
    else:
        date = check_weekday(date)  # type: ignore
        if _is_session(date) is False:  # type: ignore
            date = (to_datetime(date) + timedelta(days=1)).strftime("%Y-%m-%d")  # type: ignore
        date = check_weekday(date)  # type: ignore
        if _is_session(date) is False:  # type: ignore
            date = (to_datetime(date) + timedelta(days=1)).strftime("%Y-%m-%d")  # type: ignore

        EOD_URL = BASE_URL + f"{symbol}&from={date}&to={date}&dnld=1#quotes"

    r = await get_data_from_url(EOD_URL, use_cache=use_cache)  # type: ignore

    if r is None:
        raise OpenBBError("Error with the request, no data was returned.")

    data = read_csv(StringIO(r))
    if data.empty:
        raise OpenBBError(
            f"No data found for, {symbol}, on, {date}."
            "The symbol may not have been listed, or traded options, before that date."
        )

    data["contractSymbol"] = data["Symbol"]

    data["optionType"] = data["Call/Put"].replace(0, "call").replace(1, "put")

    data = data.drop(
        columns=[
            "Symbol",
            "Class Symbol",
            "Root Symbol",
            "Underlying Symbol",
            "Ins. Type",
            "Call/Put",
        ]
    )

    cols = [
        "eod_date",
        "strike",
        "expiration",
        "closeBid",
        "closeAsk",
        "closeBidSize",
        "closeAskSize",
        "lastTradePrice",
        "volume",
        "prevClose",
        "change",
        "open",
        "high",
        "low",
        "totalValue",
        "transactions",
        "settlementPrice",
        "openInterest",
        "impliedVolatility",
        "contractSymbol",
        "optionType",
    ]

    data.columns = cols
    data["underlying_symbol"] = symbol + ":CA"
    data["expiration"] = to_datetime(data["expiration"], format="%Y-%m-%d")
    data["eod_date"] = to_datetime(data["eod_date"], format="%Y-%m-%d")
    data["impliedVolatility"] = 0.01 * data["impliedVolatility"]

    date_ = data["eod_date"]
    temp = DatetimeIndex(data.expiration)
    temp_ = temp - date_  # type: ignore
    data["dte"] = [Timedelta(_temp_).days for _temp_ in temp_]  # type: ignore
    data = data.set_index(["expiration", "strike", "optionType"]).sort_index()
    data["eod_date"] = data["eod_date"].astype(str)
    underlying_price = data.iloc[-1]["lastTradePrice"]
    data["underlyingPrice"] = underlying_price
    data = data.reset_index()
    data = data[data["strike"] != 0]
    data["expiration"] = to_datetime(data["expiration"]).dt.strftime("%Y-%m-%d")

    data.columns = [to_snake_case(c) for c in data.columns.to_list()]

    return data