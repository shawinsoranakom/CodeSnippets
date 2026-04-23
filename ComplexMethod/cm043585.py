async def aextract_data(
        query: YFinancePriceTargetConsensusQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Extract the raw data from YFinance."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        from openbb_core.provider.utils.errors import EmptyDataError
        from warnings import warn
        from yfinance import Ticker

        symbols = query.symbol.split(",")  # type: ignore
        results = []
        fields = [
            "symbol",
            "currentPrice",
            "currency",
            "targetHighPrice",
            "targetLowPrice",
            "targetMeanPrice",
            "targetMedianPrice",
            "recommendationMean",
            "recommendationKey",
            "numberOfAnalystOpinions",
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
                    f"Error getting data for {symbol}: {e.__class__.__name__}: {e}"
                )
            if ticker:
                for field in fields:
                    if field in ticker:
                        result[field] = ticker.get(field, None)
                if result and result.get("numberOfAnalystOpinions") is not None:
                    results.append(result)

        tasks = [get_one(symbol) for symbol in symbols]

        await asyncio.gather(*tasks)

        if not results and not messages:
            raise EmptyDataError("No data was returned for the given symbol(s)")

        if not results and messages:
            raise OpenBBError("\n".join(messages))

        if results and messages:
            for message in messages:
                warn(message)

        return results