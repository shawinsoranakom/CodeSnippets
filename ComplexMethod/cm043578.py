async def aextract_data(
        query: YFinanceEquityProfileQueryParams,
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
            "longName",
            "exchange",
            "timeZoneFullName",
            "quoteType",
            "firstTradeDateEpochUtc",
            "currency",
            "sharesOutstanding",
            "floatShares",
            "impliedSharesOutstanding",
            "sharesShort",
            "sector",
            "industry",
            "address1",
            "city",
            "state",
            "zip",
            "country",
            "phone",
            "website",
            "fullTimeEmployees",
            "longBusinessSummary",
            "marketCap",
            "yield",
            "dividendYield",
            "beta",
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
                for field in fields:
                    if field in ticker:
                        result[
                            field.replace("dividendYield", "dividend_yield").replace(
                                "issueType", "issue_type"
                            )
                        ] = ticker.get(field, None)
                if result:
                    results.append(result)

        tasks = [get_one(symbol) for symbol in symbols]

        await asyncio.gather(*tasks)

        if not results and messages:
            raise OpenBBError("\n".join(messages))

        if not results and not messages:
            raise EmptyDataError("No data was returned for any symbol")

        if results and messages:
            for message in messages:
                warn(message)

        return results