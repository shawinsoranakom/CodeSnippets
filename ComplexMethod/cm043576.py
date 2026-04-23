async def aextract_data(
        query: YFinanceShareStatisticsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Extract the raw data from YFinance."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        from openbb_core.app.model.abstract.error import OpenBBError
        from openbb_core.provider.utils.errors import EmptyDataError
        from yfinance import Ticker

        symbols = query.symbol.split(",")
        results = []
        fields = [
            "symbol",
            "sharesOutstanding",
            "floatShares",
            "impliedSharesOutstanding",
            "sharesShort",
            "sharesShortPriorMonth",
            "sharesShortPreviousMonthDate",
            "shortRatio",
            "shortPercentOfFloat",
            "dateShortInterest",
            "heldPercentInsiders",
            "heldPercentInstitutions",
            "institutionsFloatPercentHeld",
            "institutionsCount",
        ]
        messages: list = []

        async def get_one(symbol):
            """Get the data for one ticker symbol."""
            result: dict = {}
            ticker: dict = {}
            try:
                _ticker = await asyncio.to_thread(lambda: Ticker(symbol))
                ticker = await asyncio.to_thread(lambda: _ticker.get_info())
                major_holders = await asyncio.to_thread(
                    lambda: _ticker.get_major_holders(as_dict=True).get("Value")
                )
                if major_holders:
                    ticker.update(major_holders)  # type: ignore
            except Exception as e:
                messages.append(
                    f"Error getting data for {symbol} -> {e.__class__.__name__}: {e}"
                )
            if ticker:
                for field in fields:
                    if field in ticker:
                        result[field] = ticker.get(field, None)
                if result and result.get("sharesOutstanding") is not None:
                    results.append(result)

        tasks = [get_one(symbol) for symbol in symbols]

        await asyncio.gather(*tasks)

        if not results and messages:
            raise OpenBBError("\n".join(messages))

        if not results and not messages:
            raise EmptyDataError("No data was returned for the given symbol(s).")

        if results and messages:
            for message in messages:
                warn(message)

        return results