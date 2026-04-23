async def aextract_data(
        query: YFinanceKeyMetricsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Extract the raw data from YFinance."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        from openbb_core.app.model.abstract.error import OpenBBError
        from openbb_core.provider.utils.errors import EmptyDataError
        from warnings import warn
        from yfinance import Ticker

        symbols = query.symbol.split(",")
        results = []
        fields = [
            "symbol",
            "marketCap",
            "trailingPE",
            "forwardPE",
            "pegRatio",
            "trailingPegRatio",
            "earningsQuarterlyGrowth",
            "earningsGrowth",
            "revenuePerShare",
            "revenueGrowth",
            "cashPerShare",
            "quickRatio",
            "currentRatio",
            "debtToEquity",
            "grossMargins",
            "ebitdaMargins",
            "operatingMargins",
            "profitMargins",
            "returnOnAssets",
            "returnOnEquity",
            "dividendYield",
            "fiveYearAvgDividendYield",
            "payoutRatio",
            "bookValue",
            "priceToBook",
            "enterpriseValue",
            "enterpriseToRevenue",
            "enterpriseToEbitda",
            "overallRisk",
            "auditRisk",
            "boardRisk",
            "compensationRisk",
            "shareHolderRightsRisk",
            "beta",
            "52WeekChange",
            "financialCurrency",
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
            if not ticker:
                messages.append(f"No data found for {symbol}")
            elif ticker:
                for field in fields:
                    if field in ticker:
                        result[field] = ticker.get(field, None)
                if result and result.get("52WeekChange") is not None:
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