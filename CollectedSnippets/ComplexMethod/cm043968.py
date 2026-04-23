async def aextract_data(
        query: FMPCompanyNewsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the FMP endpoint."""
        # pylint: disable=import-outside-toplevel
        from openbb_fmp.utils.helpers import get_data_many

        api_key = credentials.get("fmp_api_key") if credentials else ""
        limit = query.limit if query.limit else 250
        page = query.page if query.page else 0
        base_url = "https://financialmodelingprep.com/stable/news/"
        symbols = query.symbol

        if query.press_release:
            base_url += "press-releases?"
        else:
            base_url += "stock?"

        url = base_url + f"symbols={symbols}"

        if query.start_date:
            url += f"&from={query.start_date}"

        if query.end_date:
            url += f"&to={query.end_date}"

        url += f"&limit={limit}&page={page}&apikey={api_key}"

        response = await get_data_many(url, **kwargs)

        if not response:
            raise EmptyDataError()

        return sorted(response, key=lambda x: x["publishedDate"], reverse=True)