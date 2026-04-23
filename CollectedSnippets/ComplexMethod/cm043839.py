async def aextract_data(
        query: TiingoEquityHistoricalQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the Tiingo endpoint."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        from openbb_core.provider.utils.helpers import get_querystring
        from openbb_tiingo.utils.helpers import get_data

        api_key = credentials.get("tiingo_token") if credentials else ""

        base_url = (
            "https://api.tiingo.com/tiingo/daily"
            if query.interval in ["1d", "1W", "1M", "1Y"]
            else "https://api.tiingo.com/iex"
        )
        query_str = get_querystring(
            query.model_dump(by_alias=True), ["symbol", "interval"]
        )
        frequency_dict = {
            "1d": "daily",
            "1W": "weekly",
            "1M": "monthly",
            "1Y": "annually",
        }
        frequency = (
            frequency_dict.get(query.interval, "")
            if query.interval in frequency_dict
            else query.interval
        )
        cols_str = "&columns=open,high,low,close,volume"

        if frequency.endswith("m"):
            frequency = f"{frequency[:-1]}min"
            query_str = query_str + cols_str
        elif frequency == "h":
            frequency = f"{frequency[:-1]}hour"
            query_str = query_str + cols_str

        results: list = []
        messages: list = []

        async def get_one(symbol):
            """Get data for one symbol."""
            url = f"{base_url}/{symbol}/prices?{query_str}&resampleFreq={frequency}&token={api_key}"
            data = None
            try:
                data = await get_data(url)
            except UnauthorizedError as e:
                raise e from e
            except OpenBBError as e:
                if (
                    e.original
                    and isinstance(e.original, str)
                    and "ticker" in e.original.lower()
                ):
                    messages.append(e.original)
                else:
                    messages.append(f"{symbol}: {e.original}")

            if isinstance(data, list):
                if "," in query.symbol:
                    for d in data:
                        d["symbol"] = symbol
                results.extend(data)

        symbols = query.symbol.split(",")
        await asyncio.gather(*[get_one(symbol) for symbol in symbols])

        if not results and messages:
            raise OpenBBError(f"{messages}")

        if not results and not messages:
            raise EmptyDataError("The request was returned empty.")

        if results and messages:
            for message in messages:
                warn(message)

        return results