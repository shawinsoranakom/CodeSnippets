async def aextract_data(
        query: IntrinioHistoricalMarketCapQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the Intrinio endpoint."""
        # pylint: disable=import-outside-toplevel
        import asyncio  #  noqa
        from openbb_core.provider.utils.helpers import amake_request
        from openbb_intrinio.utils.helpers import response_callback
        from warnings import warn

        api_key = credentials.get("intrinio_api_key") if credentials else ""
        base_url = "https://api-v2.intrinio.com/historical_data/"
        frequency = f"frequency={query.interval}ly&" if query.interval != "day" else ""
        start_date = query.start_date
        end_date = query.end_date
        results: list = []
        messages: list = []
        symbols = query.symbol.split(",")

        async def get_one(symbol):
            """Get data for one symbol."""
            url_params = (
                f"{symbol}/marketcap?{frequency}start_date={start_date}"
                f"&end_date={end_date}&page_size=10000"
                f"&api_key={api_key}"
            )
            url = f"{base_url}{url_params}"
            try:
                response = await amake_request(url, response_callback=response_callback)
            except OpenBBError as e:
                if "Cannot look up this item/identifier combination" in str(e):
                    msg = f"Symbol not found: {symbol}"
                    messages.append(msg)
                    return
                raise e from e

            if not isinstance(response, dict):
                raise OpenBBError(
                    f"Unexpected response format, expected a dictionary, got {response.__class__.__name__}"
                )

            if not response:
                msg = f"No data found for symbol: {symbol}"
                messages.append(msg)

            if response.get("historical_data"):
                data = response.get("historical_data", {})
                result = [
                    {"symbol": symbol, **item} for item in data if item.get("value")
                ]
                results.extend(result)

            return

        await asyncio.gather(*[get_one(symbol) for symbol in symbols])

        if messages and not results:
            raise OpenBBError(messages)

        if messages and results:
            for message in messages:
                warn(message)

        if not results:
            raise EmptyDataError("The response was returned empty.")

        return results