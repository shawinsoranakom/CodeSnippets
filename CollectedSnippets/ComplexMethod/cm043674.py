async def aextract_data(
        query: IntrinioIncomeStatementQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the Intrinio endpoint."""
        api_key = credentials.get("intrinio_api_key") if credentials else ""
        statement_code = "income_statement"
        if query.period in ["quarter", "annual"]:
            period_type = "FY" if query.period == "annual" else "QTR"
        elif query.period in ["ttm", "ytd"]:
            period_type = query.period.upper()
        else:
            raise OpenBBError(f"Period '{query.period}' not supported.")

        data_tags = [
            "ebit",
            "ebitda",
            "ebitdamargin",
            "pretaxincomemargin",
            "grossmargin",
        ]

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

        fiscal_periods = [
            f"{item['fiscal_year']}-{item['fiscal_period']}"
            for item in fundamentals_data
        ]
        fiscal_periods = fiscal_periods[: query.limit]

        async def callback(response: ClientResponse, session: ClientSession) -> dict:
            """Return the response."""
            intrinio_id = response.url.parts[-2].replace(statement_code, "calculations")

            statement_data = await response.json()

            calculations_url = f"{base_url}/fundamentals/{intrinio_id}/standardized_financials?api_key={api_key}"
            calculations_data = await session.get_json(calculations_url)

            calculations_data = [
                item
                for item in calculations_data.get("standardized_financials", [])  # type: ignore
                if item["data_tag"]["tag"] in data_tags
            ]

            return {
                "period_ending": statement_data["fundamental"]["end_date"],  # type: ignore
                "fiscal_period": statement_data["fundamental"]["fiscal_period"],  # type: ignore
                "fiscal_year": statement_data["fundamental"]["fiscal_year"],  # type: ignore
                "financials": statement_data["standardized_financials"] + calculations_data,  # type: ignore
            }

        intrinio_id = f"{query.symbol}-{statement_code}"
        urls = [
            f"{base_url}/fundamentals/{intrinio_id}-{period}/standardized_financials?api_key={api_key}"
            for period in fiscal_periods
        ]

        return await amake_requests(urls, callback, **kwargs)