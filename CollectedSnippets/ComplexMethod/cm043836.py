async def aextract_data(
        query: TiingoCurrencyHistoricalQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the Tiingo endpoint."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        from openbb_core.provider.utils.helpers import get_querystring
        from openbb_tiingo.utils.helpers import get_data
        from pandas import to_datetime

        api_key = credentials.get("tiingo_token") if credentials else ""
        base_url = "https://api.tiingo.com/tiingo/fx"
        query_str = get_querystring(
            query.model_dump(by_alias=False), ["tickers", "resampleFreq"]
        )

        query_str = get_querystring(
            query.model_dump(by_alias=True), ["symbol", "interval"]
        )

        if query.interval.endswith("m"):
            frequency = f"{query.interval[:-1]}min"
        elif query.interval.endswith("h"):
            frequency = f"{query.interval[:-1]}hour"
        elif query.interval.endswith("d"):
            frequency = f"{query.interval[:-1]}day"
        else:
            frequency = "1day"

        results: list = []
        messages: list = []
        symbols = query.symbol.split(",")

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
                for d in data:
                    ticker = d.pop("ticker", None)
                    if ticker and len(symbols) > 1:
                        d["ticker"] = d["ticker"].upper()

                    if query.interval.endswith("d"):
                        d["date"] = to_datetime(d["date"]).date()
                    else:
                        d["date"] = to_datetime(d["date"], utc=True)

                results.extend(data)

        await asyncio.gather(*[get_one(symbol) for symbol in symbols])

        if not results and messages:
            raise OpenBBError(f"{messages}")

        if not results and not messages:
            raise EmptyDataError("The request was returned empty.")

        if results and messages:
            for message in messages:
                warn(message)

        return results