async def aextract_data(
        query: YFinanceEtfInfoQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Extract the raw data from YFinance."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        from openbb_core.app.model.abstract.error import OpenBBError
        from openbb_core.provider.utils.errors import EmptyDataError
        from openbb_core.provider.utils.helpers import (
            safe_fromtimestamp,
        )
        from warnings import warn
        from yfinance import Ticker

        symbols = query.symbol.split(",")
        results: list = []
        fields = [
            "symbol",
            "quoteType",
            "legalType",
            "longName",
            "fundFamily",
            "category",
            "exchange",
            "timeZoneFullName",
            "fundInceptionDate",
            "currency",
            "navPrice",
            "totalAssets",
            "trailingPE",
            "yield",
            "trailingAnnualDividendRate",
            "trailingAnnualDividendYield",
            "bid",
            "bidSize",
            "ask",
            "askSize",
            "open",
            "dayHigh",
            "dayLow",
            "previousClose",
            "volume",
            "averageVolume",
            "averageDailyVolume10Day",
            "fiftyTwoWeekHigh",
            "fiftyTwoWeekLow",
            "fiftyDayAverage",
            "twoHundredDayAverage",
            "ytdReturn",
            "threeYearAverageReturn",
            "fiveYearAverageReturn",
            "beta3Year",
            "longBusinessSummary",
            "firstTradeDateEpochUtc",
        ]
        messages: list = []

        async def get_one(symbol):
            """Get the data for one ticker symbol."""
            result: dict = {}
            ticker: dict = {}
            try:
                ticker = await asyncio.to_thread(lambda: Ticker(symbol).get_info())
            except Exception as e:
                messages.append(
                    f"Error getting data for {symbol} -> {e.__class__.__name__}: {e}"
                )
            if ticker:
                quote_type = ticker.pop("quoteType", "")
                if quote_type == "ETF":
                    try:
                        for field in fields:
                            if field in ticker and ticker.get(field) is not None:
                                result[field] = ticker.get(field, None)
                        if "firstTradeDateEpochUtc" in result:
                            _first_trade = result.pop("firstTradeDateEpochUtc")
                            if (
                                "fundInceptionDate" not in result
                                and _first_trade is not None
                            ):
                                result["fundInceptionDate"] = safe_fromtimestamp(
                                    _first_trade
                                )
                    except Exception as e:
                        messages.append(
                            f"Error processing data for {symbol} -> {e.__class__.__name__}: {e}"
                        )
                        result = {}
                if quote_type != "ETF":
                    messages.append(f"{symbol} is not an ETF.")
                if result:
                    results.append(result)

        tasks = [get_one(symbol) for symbol in symbols]

        await asyncio.gather(*tasks)

        if not results and not messages:
            raise EmptyDataError("No data was returned for the given symbol(s).")

        if not results and messages:
            raise OpenBBError("\n".join(messages))

        if results and messages:
            for message in messages:
                warn(message)

        return results