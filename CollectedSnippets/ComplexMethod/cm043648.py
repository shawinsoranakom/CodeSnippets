async def aextract_data(
        query: IntrinioForwardPeEstimatesQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the Intrinio endpoint."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        from openbb_core.provider.utils.errors import EmptyDataError, UnauthorizedError
        from openbb_core.provider.utils.helpers import amake_request
        from openbb_intrinio.utils.helpers import response_callback

        api_key = credentials.get("intrinio_api_key") if credentials else ""
        BASE_URL = "https://api-v2.intrinio.com/zacks/forward_pe"
        symbols = query.symbol.split(",") if query.symbol else None
        results: list[dict] = []

        async def get_one(symbol):
            """Get the data for one symbol."""
            url = f"{BASE_URL}/{symbol}?api_key={api_key}"
            try:
                data = await amake_request(
                    url, response_callback=response_callback, **kwargs
                )
            except Exception as e:
                raise OpenBBError(e) from e

            if data:
                results.append(data)  # type: ignore

        if symbols:
            try:
                gather_results = await asyncio.gather(
                    *[get_one(symbol) for symbol in symbols], return_exceptions=True
                )

                for result in gather_results:
                    if isinstance(result, UnauthorizedError):
                        raise result
                    if isinstance(result, OpenBBError):
                        raise result

                if not results:
                    raise EmptyDataError(
                        f"There were no results found for any of the given symbols. -> {symbols}"
                    )
                return results
            except Exception as e:
                raise OpenBBError(
                    f"Error in Intrinio request -> {e} -> {symbols}"
                ) from e

        async def fetch_callback(response, session):
            """Use callback for pagination."""
            data = await response.json()
            error = data.get("error", None)

            if error:
                message = data.get("message", "")
                if "api key" in message.lower() or "view this data" in error.lower():
                    raise UnauthorizedError(
                        f"Unauthorized Intrinio request -> {message} -> {error}"
                    )
                raise OpenBBError(f"Error: {error} -> {message}")

            forward_pe = data.get("forward_pe")

            if forward_pe and len(forward_pe) > 0:  # type: ignore
                results.extend(forward_pe)  # type: ignore

            return results

        url = f"{BASE_URL}?page_size=10000&api_key={api_key}"
        results = await amake_request(url, response_callback=fetch_callback, **kwargs)  # type: ignore

        if not results:
            raise EmptyDataError("The request was successful but was returned empty.")

        return results