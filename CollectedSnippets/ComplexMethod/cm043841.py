async def aextract_data(
        query: TiingoWorldNewsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the tiingo endpoint."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        import math
        from openbb_core.provider.utils.helpers import get_querystring
        from openbb_tiingo.utils.helpers import get_data

        api_key = credentials.get("tiingo_token") if credentials else ""

        base_url = "https://api.tiingo.com/tiingo/news"

        query_str = get_querystring(
            query.model_dump(by_alias=False), ["limit", "offset"]
        )

        limit = query.limit if query.limit else 1000
        pages = 0
        if limit > 1000:
            pages = math.ceil(limit / 1000)
            limit = 1000
            urls = [
                f"{base_url}?{query_str}&token={api_key}&limit={limit}&offset={page * 1000 if page > 0 else 0}"
                for page in range(0, pages)
            ]
        else:
            urls = [f"{base_url}?{query_str}&token={api_key}&limit={limit}"]

        results: list = []

        async def get_one(url):
            """Get data for one URL and append results to list."""
            response = await get_data(url)
            if isinstance(response, list):
                results.extend(response)
            elif isinstance(response, dict):
                results.append(response)

        await asyncio.gather(*[get_one(url) for url in urls])

        if not results:
            raise EmptyDataError()

        return results