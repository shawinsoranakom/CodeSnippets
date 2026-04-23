async def aextract_data(
        query: IntrinioEtfPricePerformanceQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the Intrinio endpoint."""

        api_key = credentials.get("intrinio_api_key") if credentials else ""
        base_url = "https://api-v2.intrinio.com/etfs/"
        symbols = query.symbol.split(",")
        symbols = [
            symbol + ":US" if ":" not in symbol else symbol for symbol in symbols
        ]

        adjustment = (
            "split_only"
            if query.adjustment == "splits_and_dividends"
            else "split_and_dividend"
        )

        return_type = "trailing" if query.return_type == "calendar" else "calendar"

        results = []

        async def get_one(symbol: str, **kwargs):
            """Get data for one symbol."""

            url = f"{base_url}{symbol}/stats?api_key={api_key}"
            result = await amake_request(url, **kwargs)

            if "message" in result and result["message"] != []:  # type: ignore
                warn(f"Symbol Error: {symbol} - {result['message']}")  # type: ignore
                return
            _ = result.pop("message", None)  # type: ignore
            _ = result.pop("messages", None)  # type: ignore

            data = {}
            etf = result.pop("etf", {})  # type: ignore
            data["symbol"] = etf.get("ticker")
            # These items will be kept regardless of the adjustment and return_type.
            keep = ["volatility", "month", "year_to_date"]
            for k, v in result.copy().items():  # type: ignore
                if not any(substring in k for substring in keep):
                    _ = result.pop(k, None) if adjustment in k else None  # type: ignore
                    _ = result.pop(k, None) if return_type in k else None  # type: ignore
                if k in result:
                    data[ETF_PERFORMANCE_MAP.get(k, k)] = v
            # Get an additional set of data to combine with the first set.
            analytics_url = (
                f"https://api-v2.intrinio.com/etfs/{symbol}/analytics?api_key={api_key}"
            )
            if data:
                analytics = await amake_request(analytics_url, **kwargs)
                if "messages" in analytics and analytics["messages"] != []:  # type: ignore
                    warn(
                        f"Symbol Error: {analytics['messages']}"  # type: ignore
                        + f"for {etf.get('ticker')}"  # type: ignore
                    )
                    return
                # Remove the duplicate data from the analytics response.
                _ = analytics.pop("messages", None)  # type: ignore
                _ = analytics.pop("etf", None)  # type: ignore
                _ = analytics.pop("date", None)  # type: ignore

                data.update(analytics)  # type: ignore

            results.append(data)

        tasks = [get_one(symbol, **kwargs) for symbol in symbols]

        await asyncio.gather(*tasks)

        if not results:
            raise EmptyDataError("No data was returned.")

        # Undo any formatting changes made to the symbols before sorting.
        symbols = query.symbol.replace(":US", "").split(",")

        return sorted(
            results,
            key=(lambda item: (symbols.index(item.get("symbol", len(symbols))))),
        )