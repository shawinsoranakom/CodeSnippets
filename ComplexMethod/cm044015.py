async def aextract_data(
        query: BenzingaCompanyNewsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Extract data."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        import math
        from openbb_core.provider.utils.helpers import amake_request, get_querystring
        from openbb_benzinga.utils.helpers import response_callback

        token = credentials.get("benzinga_api_key") if credentials else ""
        base_url = "https://api.benzinga.com/api/v2/news"
        query.limit = query.limit if query.limit else 2500
        model = query.model_dump(by_alias=True)
        model["sort"] = (
            f"{query.sort}:{query.order}" if query.sort and query.order else ""
        )
        querystring = get_querystring(model, ["order", "pageSize"])
        page_size = 100 if query.limit and query.limit > 100 else query.limit
        pages = math.ceil(query.limit / page_size) if query.limit else 1
        urls = [
            f"{base_url}?{querystring}&page={page}&pageSize={page_size}&token={token}"
            for page in range(pages)
        ]
        results: list = []

        async def get_one(url):
            """Get data for one url."""
            try:
                response = await amake_request(
                    url,
                    response_callback=response_callback,
                    **kwargs,
                )
                if response:
                    results.extend(response)
            except (OpenBBError, UnauthorizedError) as e:
                raise e from e

        await asyncio.gather(*[get_one(url) for url in urls])

        if not results:
            raise EmptyDataError("The request was returned empty.")

        return sorted(
            results, key=lambda x: x.get("created"), reverse=query.order == "desc"
        )[: query.limit if query.limit else len(results)]