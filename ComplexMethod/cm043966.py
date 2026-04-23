async def aextract_data(
        query: FMPDiscoveryFilingsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the FMP endpoint."""
        # pylint: disable=import-outside-toplevel
        import math  # noqa
        from openbb_core.provider.utils.helpers import amake_requests, get_querystring

        api_key = credentials.get("fmp_api_key") if credentials else ""
        data: list[dict] = []
        limit = query.limit or 10000
        base_url = (
            "https://financialmodelingprep.com/stable/sec-filings-search/form-type"
            if query.form_type
            else "https://financialmodelingprep.com/stable/sec-filings-financials/"
        )
        start_date = (
            query.start_date
            or (datetime.now() - timedelta(days=89 if query.form_type else 2)).date()
        )
        end_date = query.end_date or datetime.now().date()
        query.start_date = start_date
        query.end_date = end_date

        query_str = get_querystring(query.model_dump(by_alias=True), ["limit"])

        # FMP only allows 1000 results per page
        pages = math.ceil(limit / 1000)

        urls = [
            f"{base_url}?{query_str}&page={page}&limit=1000&apikey={api_key}"
            for page in range(pages)
        ]

        data = await amake_requests(urls, **kwargs)

        return sorted(data, key=lambda x: x["acceptedDate"], reverse=True)