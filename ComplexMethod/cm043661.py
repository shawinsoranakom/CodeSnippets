async def aextract_data(
        query: IntrinioFinancialRatiosQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the Intrinio endpoint."""
        api_key = credentials.get("intrinio_api_key") if credentials else ""
        statement_code = "calculations"
        if query.period in ["quarter", "annual"]:
            period_type = "FY" if query.period == "annual" else "QTR"
        elif query.period in ["ttm", "ytd"]:
            period_type = query.period.upper()
        else:
            raise OpenBBError(f"Period '{query.period}' not supported.")

        fundamentals_data: dict = {}

        base_url = "https://api-v2.intrinio.com"
        fundamentals_url = (
            f"{base_url}/companies/{query.symbol}"
            f"/fundamentals?statement_code={statement_code}&type={period_type}"
        )
        if query.fiscal_year is not None:
            if query.fiscal_year < 2008:
                warn("Financials data is only available from 2008 and later.")
                query.fiscal_year = 2008
            fundamentals_url = fundamentals_url + f"&fiscal_year={query.fiscal_year}"
        fundamentals_url = fundamentals_url + f"&api_key={api_key}"
        fundamentals_data = (await get_data_one(fundamentals_url, **kwargs)).get(
            "fundamentals", []
        )
        ids = [item["id"] for item in fundamentals_data]
        ids = ids[: query.limit]

        async def callback(response: ClientResponse, _: Any) -> dict:
            """Return the response."""
            statement_data = await response.json()
            return {
                "period_ending": statement_data["fundamental"]["end_date"],  # type: ignore
                "fiscal_year": statement_data["fundamental"]["fiscal_year"],  # type: ignore
                "fiscal_period": statement_data["fundamental"]["fiscal_period"],  # type: ignore
                "calculations": statement_data["standardized_financials"],  # type: ignore
            }

        urls = [
            f"https://api-v2.intrinio.com/fundamentals/{id}/standardized_financials?api_key={api_key}"
            for id in ids
        ]

        return await amake_requests(urls, callback, **kwargs)