async def aextract_data(
        query: IntrinioCompanyFilingsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw data from the Intrinio endpoint."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError, OpenBBError
        from openbb_core.provider.utils.helpers import (
            get_async_requests_session,
            get_querystring,
        )

        api_key = credentials.get("intrinio_api_key") if credentials else ""

        base_url = "https://api-v2.intrinio.com/companies"
        query_str = get_querystring(
            query.model_dump(by_alias=True), ["symbol", "limit", "page_size"]
        )
        url = f"{base_url}/{query.symbol}/filings?{query_str}&page_size={query.limit or 10000}&api_key={api_key}"
        results: list = []
        metadata: dict = {}
        session = await get_async_requests_session()

        async with await session.get(url) as response:
            if response.status != 200:
                raise OpenBBError(
                    f"Error fetching data from Intrinio: {response.status} -> {response.text}"
                )
            result = await response.json()
            if filings := result.get("filings", []):
                results.extend(filings)

            metadata = result.get("company", {})

            while next_page := result.get("next_page"):
                url += f"&next_page={next_page}"
                async with await session.get(url) as next_response:
                    if response.status != 200:
                        raise OpenBBError(
                            f"Error fetching data from Intrinio: {response.status} -> {response.text}"
                        )
                    result = await next_response.json()
                    if filings := result.get("filings", []):
                        results.extend(filings)

        if not results:
            raise EmptyDataError("No data was returned for the symbol provided.")

        return {"data": results, "metadata": metadata}