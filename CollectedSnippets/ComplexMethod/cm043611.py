async def get_vx_by_date(
    date: str | list[str],
    vx_type: Literal["am", "eod"] = "eod",
    use_cache: bool = True,
) -> "DataFrame":
    """Get VX futures by date(s).

    Parameters
    ----------
    date : str or List[str]
        The date(s) to get VX futures for.
    vx_type : Literal["am", "eod"]
        The type of VX futures to get. Default is "eod".
            am: Mid-morning TWAP value
            eod: End-of-day value
    use_cache : bool
        Whether to use the cache. Default is True. Cache is only used for symbol mapping.

    Returns
    -------
    DataFrame
        Categorical DataFrame with VX futures data for the given date(s).
    """
    # pylint: disable=import-outside-toplevel
    from datetime import datetime, timedelta  # noqa
    from openbb_core.app.model.abstract.error import OpenBBError
    from openbb_core.provider.utils.errors import EmptyDataError
    from openbb_cboe.models.equity_historical import CboeEquityHistoricalFetcher
    from pandas import Categorical, DataFrame, DatetimeIndex, concat, isna, to_datetime

    if vx_type not in ["am", "eod"]:
        raise OpenBBError("'vx_type' must be one of: 'am', 'eod'")

    df = DataFrame()
    start_date = ""
    end_date = ""
    symbols = list(get_vx_symbols().values()) if vx_type == "eod" else VX_AM_SYMBOLS
    dates = date.split(",") if isinstance(date, str) else date
    dates = sorted([check_date(to_datetime(d)) for d in dates])
    today = check_date(datetime.today()).strftime("%Y-%m-%d")

    if len(dates) == 1:
        new_date = check_date(to_datetime(dates[0]))
        if new_date.strftime("%Y-%m-%d") == today:
            df = await get_vx_current(vx_type=vx_type)
            df["date"] = new_date.strftime("%Y-%m-%d")
            return df

        end_date = new_date.strftime("%Y-%m-%d")
        start_date = (check_date(new_date - timedelta(days=1))).strftime("%Y-%m-%d")
    else:
        start_date = check_date(dates[0]).strftime("%Y-%m-%d")
        end_date = check_date(dates[-1]).strftime("%Y-%m-%d")

    # The data from the current date is not available in the historical data,
    # so we need to get it separately, if required.
    current_data = DataFrame()

    if end_date == today:
        current_data = await get_vx_current(vx_type=vx_type)
        current_data["date"] = end_date
        current_data["symbol"] = [
            "VX1",
            "VX2",
            "VX3",
            "VX4",
            "VX5",
            "VX6",
            "VX7",
            "VX8",
            "VX9",
        ]

    data = await CboeEquityHistoricalFetcher.fetch_data(
        {
            "symbol": ",".join(symbols),
            "start_date": start_date,
            "end_date": end_date,
            "use_cache": use_cache,
        }
    )
    df = DataFrame([d.model_dump() for d in data])  # type: ignore
    df = df.set_index("date").sort_index()

    df.index = df.index.astype(str)
    df.index = DatetimeIndex(df.index)
    dates_list = DatetimeIndex(dates)
    symbols = df.symbol.unique().tolist()
    df = df.reset_index().pivot(columns="symbol", values="close", index="date").copy()  # type: ignore
    if vx_type == "am":
        df = df.dropna(how="any")

    nearest_dates = []
    for date_ in dates_list:
        nearest_date = df.index.asof(date_)
        if isna(nearest_date):
            differences = abs(df.index - date_)  # type: ignore
            min_diff_index = differences.argmin()
            nearest_date = df.index[min_diff_index]
        nearest_dates.append(nearest_date)
    nearest_dates = DatetimeIndex(nearest_dates)

    # Filter for only the nearest dates
    df = df[df.index.isin(nearest_dates)]
    df = df.fillna("N/A").replace("N/A", None)
    output = DataFrame()
    df.index = df.index.astype(str)
    # For each date, we need to arrange VX1 - VX9 according to the relative front month.
    for _date in df.index.tolist():
        temp = df.filter(like=_date, axis=0).copy()
        current_symbols = list(get_vx_symbols(date=_date).values())[:9]
        current_symbols = VX_AM_SYMBOLS if vx_type == "am" else current_symbols
        temp = temp.filter(items=current_symbols, axis=1)
        current_month = get_front_month(_date)
        current_months = get_months(current_month)
        current_year = int(_date.split("-")[0])
        expirations: list = []
        for month in list(current_months.values())[:9]:
            new_year = month == 1
            current_year = (
                current_year + 1 if new_year and current_month != 1 else current_year
            )
            new_month = "0" + str(month) if month < 10 else str(month)  # type: ignore
            expirations.append(f"{current_year}-{new_month}")
        flattened = temp.reset_index().melt(
            id_vars="date", var_name="expiration", value_name="price"
        )
        if vx_type == "eod":
            vx_symbols = {v: k for k, v in get_vx_symbols(date=_date).items()}
        elif vx_type == "am":
            vx_symbols = {item: item.replace("TWLV", "VX") for item in VX_AM_SYMBOLS}
        flattened["symbol"] = flattened.expiration.map(vx_symbols)
        flattened.expiration = expirations
        flattened = flattened.dropna(how="any", subset=["price"])

        output = concat([output, flattened])

    if not current_data.empty and current_data.date[0] not in output.date.unique():
        output = concat([output, current_data])

    if output.empty:
        raise EmptyDataError()

    output = output.sort_values("date")
    dates = DatetimeIndex(dates)
    if dates[-1] != nearest_dates[-1] and not current_data.empty:
        output = output[output.date != nearest_dates[-1].strftime("%Y-%m-%d")]  # type: ignore
    output["symbol"] = Categorical(
        output["symbol"],
        categories=sorted(output.symbol.unique().tolist()),
        ordered=True,
    )
    output = (
        output.sort_values(by=["date", "symbol"])
        .reset_index(drop=True)
        .dropna(how="any")
    )

    return output