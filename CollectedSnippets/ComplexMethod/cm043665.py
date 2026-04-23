async def aextract_data(
        query: IntrinioForwardEbitdaEstimatesQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the Intrinio endpoint."""
        api_key = credentials.get("intrinio_api_key") if credentials else ""
        BASE_URL = (
            "https://api-v2.intrinio.com/zacks/ebitda_consensus?"
            + f"page_size=10000&api_key={api_key}"
        )
        symbols = query.symbol.split(",") if query.symbol else None
        query_str = get_querystring(query.model_dump(by_alias=True), ["symbol"])
        results: list[dict] = []

        async def get_one(symbol):
            """Get the data for one symbol."""
            url = f"{BASE_URL}&identifier={symbol}"
            url = url + f"&{query_str}" if query_str else url
            data = await amake_request(
                url, response_callback=response_callback, **kwargs
            )
            consensus = (
                data.get("ebitda_consensus")
                if isinstance(data, dict) and "ebitda_consensus" in data
                else []
            )
            if not data or not consensus:
                warn(f"Symbol Error: No data found for {symbol}")
            if consensus:
                results.extend(consensus)

        if symbols:
            await asyncio.gather(*[get_one(symbol) for symbol in symbols])
            if not results:
                raise EmptyDataError(f"No results were found. -> {query.symbol}")
            return results

        async def fetch_callback(response, session):
            """Use callback for pagination."""
            data = await response.json()
            error = data.get("error", None)
            if error:
                message = data.get("message", "")
                if "api key" in message.lower():
                    raise UnauthorizedError(
                        f"Unauthorized Intrinio request -> {message}"
                    )
                raise OpenBBError(f"Error: {error} -> {message}")

            estimates = data.get("ebitda_consensus", [])  # type: ignore
            if estimates and len(estimates) > 0:
                results.extend(estimates)
                while data.get("next_page"):  # type: ignore
                    next_page = data["next_page"]  # type: ignore
                    next_url = f"{url}&next_page={next_page}"
                    data = await amake_request(next_url, session=session, **kwargs)
                    consensus = (
                        data.get("ebitda_consensus")
                        if isinstance(data, dict) and "ebitda_consensus" in data
                        else []
                    )
                    if consensus:
                        results.extend(consensus)  # type: ignore
            return results

        url = f"{BASE_URL}&{query_str}" if query_str else BASE_URL

        results = await amake_request(url, response_callback=fetch_callback, **kwargs)  # type: ignore

        if not results:
            raise EmptyDataError("The request was successful but was returned empty.")

        return results