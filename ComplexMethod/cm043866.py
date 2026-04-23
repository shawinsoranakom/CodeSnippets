async def aextract_data(
        query: EiaShortTermEnergyOutlookQueryParams,
        credentials: dict[str, Any] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Extract the data from the EIA API."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        from openbb_core.provider.utils.helpers import amake_request
        from openbb_us_eia.utils.helpers import response_callback

        api_key = credentials.get("eia_api_key") if credentials else ""
        frequency_dict = {
            "month": "monthly",
            "quarter": "quarterly",
            "annual": "annual",
        }
        frequency = frequency_dict[query.frequency]
        base_url = f"https://api.eia.gov/v2/steo/data/?api_key={api_key}&frequency={frequency}&data[0]=value"
        urls: list[str] = []
        start_date: str = ""
        end_date: str = ""

        # Format the dates based on the frequency.
        def resample_to_quarter(dt) -> str:
            """Resample a date to a string formatted as 'YYYY-QX'."""
            year = dt.year
            quarter = (dt.month - 1) // 3 + 1
            return f"{year}-Q{quarter}"

        if query.start_date is not None and frequency == "monthly":
            start_date = f"&start={query.start_date.strftime('%Y-%m')}"
        elif query.start_date is not None and frequency == "quarterly":
            start_date = f"&start={resample_to_quarter(query.start_date)}"
        elif query.start_date is not None and frequency == "annual":
            start_date = f"&start={query.start_date.strftime('%Y')}"

        if query.end_date is not None and frequency == "monthly":
            end_date = f"&end={query.end_date.strftime('%Y-%m')}"
        elif query.end_date is not None and frequency == "quarterly":
            end_date = f"&end={resample_to_quarter(query.end_date)}"
        elif query.end_date is not None and frequency == "annual":
            end_date = f"&end={query.end_date.strftime('%Y')}"

        # We chunk the request to avoid pagination and make the query execution faster.
        symbols = (
            query.symbol.upper().split(",")
            if query.symbol
            else [d.upper() for d in SteoTableMap[query.table]]
        )
        seen = set()
        unique_symbols: list = []
        for symbol in symbols:
            if symbol not in seen:
                unique_symbols.append(symbol)
                seen.add(symbol)
        symbols = unique_symbols

        def encode_symbols(symbol: str):
            """Encode a chunk of symbols to be used in a URL"""
            prefix = "&facets[seriesId][]="
            return prefix + symbol.upper()

        for i in range(0, len(symbols), 10):
            url_symbols: str = ""
            symbols_chunk = symbols[i : i + 10]
            for symbol in symbols_chunk:
                url_symbols += encode_symbols(symbol)
            url = f"{base_url}{url_symbols}{start_date}{end_date}&offset=0&length=5000"
            urls.append(url)

        results: list[dict] = []
        messages: list[str] = []

        async def get_one(url):
            """Response callback function."""
            res = await amake_request(url, response_callback=response_callback)
            data = res.get("response", {}).get("data", [])  # type: ignore
            if not data:
                series_id = res.get("request", {}).get("params", {}).get("facets", {}).get("seriesId", [])  # type: ignore
                masked_url = url.replace(api_key, "API_KEY")
                messages.append(f"No data returned for {series_id or masked_url}")
            if data:
                results.extend(data)
            response_total = int(res.get("response", {}).get("total", 0))  # type: ignore
            n_results = len(data)
            # After conservatively chunking the request, we may still need to paginate.
            # This is mostly out of an abundance of caution.
            if response_total > 5000 and n_results == 5000:
                offset = 5000
                url = url.replace("&offset=0", f"&offset={offset}")
                while n_results < response_total:
                    additional_response = await amake_request(url)
                    additional_data = additional_response.get("response", {}).get("data", [])  # type: ignore
                    if not additional_data:
                        series_id = (
                            res.get("request", {}).get("params", {}).get("facets", {}).get("seriesId", [])  # type: ignore
                        )
                        masked_url = url.replace(api_key, "API_KEY")
                        messages.append(
                            f"No additional data returned for {series_id or masked_url}"
                        )
                    if additional_data:
                        results.extend(additional_data)
                    n_results += len(additional_data)
                    url = url.replace(f"&offset={offset}", f"&offset={offset + 5000}")
                    offset += 5000

        try:
            await asyncio.gather(*[get_one(url) for url in urls])
        except Exception as e:
            raise OpenBBError(f"Error fetching data from the EIA API -> {e}") from e

        if not results and not messages:
            raise EmptyDataError(
                "The request was returned empty with no error messages."
            )
        if not results and messages:
            raise OpenBBError("\n".join(messages))
        if results and messages:
            warn("\n".join(messages))

        return results