async def aextract_data(
        query: FMPCompanyFilingsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the FMP endpoint."""
        # pylint: disable=import-outside-toplevel
        from openbb_fmp.utils.helpers import get_data_many

        api_key = credentials.get("fmp_api_key") if credentials else ""

        base_url = "https://financialmodelingprep.com/stable/sec-filings-search"
        url: str = ""

        if query.symbol and not query.cik:
            url = base_url + f"/symbol?symbol={query.symbol}"
        elif query.cik:
            url = base_url + f"/cik?cik={query.cik}"

        if not url:
            raise ValueError("Either symbol or cik must be provided.")

        start_date = (
            query.start_date
            if query.start_date
            else dateType.today() - timedelta(days=360)
        )
        url += f"&from={start_date}"
        end_date = query.end_date if query.end_date else dateType.today()
        url += f"&to={end_date}"
        url += f"&page={query.page}&limit={query.limit}&apikey={api_key}"

        return await get_data_many(url, **kwargs)