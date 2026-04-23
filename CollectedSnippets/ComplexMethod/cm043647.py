async def aextract_data(
        query: IntrinioOptionsChainsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw data from the Intrinio endpoint."""
        # pylint: disable=import-outside-toplevel
        from datetime import timedelta  # noqa
        from openbb_core.provider.utils.helpers import (
            amake_requests,
            get_querystring,
        )
        from openbb_intrinio.utils.helpers import (
            get_data_many,
            get_weekday,
            response_callback,
        )

        api_key = credentials.get("intrinio_api_key") if credentials else ""

        base_url = "https://api-v2.intrinio.com/options"

        date = query.date if query.date is not None else datetime.now().date()
        date = get_weekday(date)

        if query.symbol in ["SPX", "^SPX", "^GSPC"]:
            query.symbol = "SPX"
            warn("For weekly SPX options, use the symbol SPXW instead of SPX.")

        async def get_urls(date: str) -> list[str]:
            """Return the urls for the given date."""
            date = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)).strftime(
                "%Y-%m-%d"
            )
            url = (
                f"{base_url}/expirations/{query.symbol}/"
                f"{'eod' if query.delay == 'eod' else 'realtime'}?"
                f"{'after=' + date + '&' if query.delay == 'eod' else 'source=' + query.delay + '&'}"
                f"api_key={api_key}"
            )
            expirations = await get_data_many(url, "expirations", **kwargs)

            def generate_url(expiration) -> str:
                url = f"{base_url}/chain/{query.symbol}/{expiration}/"
                if query.date is not None:
                    query_string = get_querystring(
                        query.model_dump(exclude_none=True),
                        [
                            "symbol",
                            "date",
                            "model",
                            "volume_greater_than",
                            "volume_less_than",
                            "moneyness",
                            "open_interest_greater_than",
                            "open_interest_less_than",
                            "show_extended_price",
                        ],
                    )
                    url = url + f"eod?date={query.date}&{query_string}"
                else:
                    if query.moneyness:
                        moneyness = (
                            "out_of_the_money"
                            if query.moneyness == "otm"
                            else "in_the_money" if query.moneyness == "itm" else "all"
                        )

                    query_string = get_querystring(
                        query.model_dump(exclude_none=True),
                        ["symbol", "date", "moneyness"],
                    )
                    url = url + f"realtime?{query_string}&moneyness={moneyness}"

                return url + f"&api_key={api_key}"

            return [generate_url(expiration) for expiration in expirations]

        async def callback(response, _) -> list:
            """Return the response."""
            response_data = await response_callback(response, _)
            return response_data.get("chain", [])  # type: ignore

        results = await amake_requests(
            await get_urls(date.strftime("%Y-%m-%d")), callback, **kwargs
        )
        # If the EOD chains are not available for the given date, try the previous day
        if not results and query.date is not None:
            date = get_weekday(date - timedelta(days=1)).strftime("%Y-%m-%d")
            urls = await get_urls(date)  # type: ignore
            results = await amake_requests(urls, response_callback=callback, **kwargs)

        if not results:
            raise OpenBBError(f"No data found for the given symbol: {query.symbol}")

        output: dict = {}
        underlying_price: dict = {}
        # If the EOD chains are requested, get the underlying price on the given date.
        if query.date is not None:
            if query.symbol.endswith("W") and query.symbol.startswith("SPX"):
                query.symbol = query.symbol[:-1]
            temp = None
            try:
                temp = await IntrinioEquityHistoricalFetcher.fetch_data(
                    {"symbol": query.symbol, "start_date": date, "end_date": date},
                    credentials,
                )
                temp = temp[0]  # type: ignore
            # If the symbol is SPX, or similar, try to get the underlying price from the index.
            except Exception as e:
                try:
                    temp = await IntrinioIndexHistoricalFetcher.fetch_data(
                        {"symbol": query.symbol, "start_date": date, "end_date": date},
                        credentials,
                    )
                    temp = temp[0]  # type: ignore
                except Exception:
                    warn(f"Failed to get underlying price for {query.symbol}: {e}")
            if temp:
                underlying_price["symbol"] = query.symbol
                underlying_price["price"] = temp.close
                underlying_price["date"] = temp.date.strftime("%Y-%m-%d")

        output = {"underlying": underlying_price, "data": results}

        return output