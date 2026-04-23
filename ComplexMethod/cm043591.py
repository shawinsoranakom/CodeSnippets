async def get_futures_curve(  # pylint: disable=too-many-return-statements
    symbol: str, date: str | list | None = None
) -> "DataFrame":
    """Get the futures curve for a given symbol.

    Parameters
    ----------
    symbol: str
        Symbol to get futures for
    date: Optional[str]
        Optional historical date to get curve for

    Returns
    -------
    DataFrame
        DataFrame with futures curve
    """
    # pylint: disable=import-outside-toplevel
    from datetime import date as dateType, datetime  # noqa
    from dateutil.relativedelta import relativedelta  # noqa
    from pandas import Categorical, DataFrame, DatetimeIndex, to_datetime  # noqa

    futures_symbols = get_futures_symbols(symbol)
    today = datetime.today().date()
    dates: list = []
    if date:
        if isinstance(date, dateType):
            date = date.strftime("%Y-%m-%d")
        if isinstance(date, list) and isinstance(date[0], dateType):
            date = [d.strftime("%Y-%m-%d") for d in date]
        dates = date.split(",") if isinstance(date, str) else date
        dates = sorted([to_datetime(d).date() for d in dates])

    if futures_symbols and (not date or len(dates) == 1 and dates[0] >= today):
        futures_quotes = await get_futures_quotes(futures_symbols)
        return futures_quotes

    if dates and futures_symbols:
        historical_futures_prices = await get_historical_futures_prices(
            futures_symbols, dates[0], dates[-1]
        )
        df = DataFrame([d.model_dump() for d in historical_futures_prices])  # type: ignore
        df = df.set_index("date").sort_index()
        df.index = df.index.astype(str)
        df.index = DatetimeIndex(df.index)
        dates_list = DatetimeIndex(dates)
        symbols = df.symbol.unique().tolist()
        expiration_dict = {symbol: get_expiration_month(symbol) for symbol in symbols}
        df = df.reset_index().pivot(columns="symbol", values="close", index="date").copy()  # type: ignore
        df = df.rename(columns=expiration_dict)
        df.columns.name = "expiration"

        # Find the nearest date in the DataFrame to each date in dates_list
        nearest_dates = [df.index.asof(date) for date in dates_list]

        # Filter for only the nearest dates
        df = df[df.index.isin(nearest_dates)]

        df = df.fillna("N/A").replace("N/A", None)

        # Flatten the DataFrame
        flattened_data = df.reset_index().melt(
            id_vars="date", var_name="expiration", value_name="price"
        )
        flattened_data = flattened_data.sort_values("date")
        flattened_data["expiration"] = Categorical(
            flattened_data["expiration"],
            categories=sorted(list(expiration_dict.values())),
            ordered=True,
        )
        flattened_data = flattened_data.sort_values(
            by=["date", "expiration"]
        ).reset_index(drop=True)
        flattened_data["date"] = flattened_data["date"].dt.strftime("%Y-%m-%d")

        return flattened_data

    if not futures_symbols:
        # pylint: disable=import-outside-toplevel
        import os  # noqa
        from contextlib import contextmanager, redirect_stderr, redirect_stdout  # noqa

        futures_data = get_futures_data()
        try:
            exchange = futures_data[futures_data["Ticker"] == symbol]["Exchange"].values[0]  # type: ignore
        except IndexError as exc:
            raise ValueError(f"Symbol {symbol} was not found.") from exc

        futures_index: list = []
        futures_curve: list = []
        futures_date: list = []
        historical_curve: list = []
        if dates:
            dates = [d.strftime("%Y-%m-%d") for d in dates]
            dates_list = DatetimeIndex(dates)

        i = 0
        empty_count = 0

        @contextmanager
        def suppress_all_output():
            with open(os.devnull, "w") as devnull, redirect_stdout(
                devnull
            ), redirect_stderr(devnull):
                yield

        with suppress_all_output():
            while empty_count < 12:
                future = today + relativedelta(months=i)
                future_symbol = (
                    f"{symbol}{MONTHS[future.month]}{str(future.year)[-2:]}.{exchange}"
                )
                data = yf_download(future_symbol)
                if data.empty:
                    empty_count += 1
                else:
                    empty_count = 0
                    if dates:
                        data = data.set_index("date").sort_index()
                        data.index = DatetimeIndex(data.index)
                        nearest_dates = [data.index.asof(date) for date in dates_list]
                        data = data[data.index.isin(nearest_dates)]
                        data.index = data.index.strftime("%Y-%m-%d")  # type: ignore
                        for dt in dates:
                            try:
                                historical_curve.append(data.loc[dt, "close"])
                                futures_date.append(dt)
                                futures_index.append(future.strftime("%Y-%m"))
                            except KeyError:
                                historical_curve.append(None)
                    else:
                        futures_index.append(future.strftime("%Y-%m"))
                        futures_curve.append(
                            data.query("close.notnull()")["close"].values[-1]
                        )

                i += 1

        if not futures_index:
            raise EmptyDataError()

        if historical_curve:
            df = DataFrame(
                {
                    "date": futures_date,
                    "price": historical_curve,
                    "expiration": futures_index,
                }
            )
            df["expiration"] = Categorical(
                df["expiration"],
                categories=sorted(list(set(futures_index))),
                ordered=True,
            )
            df = df.sort_values(by=["date", "expiration"]).reset_index(drop=True)
            if len(df.date.unique()) == 1:
                df = df.drop(columns=["date"])

            return df

    return DataFrame({"price": futures_curve, "expiration": futures_index})