async def aextract_data(
        query: IntrinioReportedFinancialsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the Intrinio endpoint."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.helpers import (
            ClientResponse,
            amake_requests,
        )
        from openbb_intrinio.utils.helpers import get_data_one
        from pandas import DataFrame

        period_type = ""
        api_key = credentials.get("intrinio_api_key") if credentials else ""
        statement_code = STATEMENT_DICT[query.statement_type]
        period_type = "FY" if query.period == "annual" else "Q"
        ids = []
        ids_url = f"https://api-v2.intrinio.com/companies/{query.symbol}/fundamentals?reported_only=true&statement_code={statement_code}"
        if query.fiscal_year is not None:
            if query.fiscal_year < 2008:
                warn("Financials data is only available from 2008 and later.")
                query.fiscal_year = 2008
            ids_url = ids_url + f"&fiscal_year={query.fiscal_year}"
        ids_url = ids_url + f"&page_size=10000&api_key={api_key}"

        fundamentals_ids = await get_data_one(ids_url, **kwargs)
        filings = DataFrame(fundamentals_ids["fundamentals"])

        _period = "" if query.period is None else period_type
        _statement = "" if statement_code is None else statement_code
        if len(filings) > 0:
            filings = filings[filings["statement_code"].str.contains(_statement)]
            if query.period == "annual":
                filings = filings[filings["fiscal_period"].str.contains(_period)]
            ids = filings.iloc[: query.limit]["id"].to_list()

        if ids == []:
            raise OpenBBError("No reports found.")

        async def callback(response: ClientResponse, _: Any) -> dict:
            """Return the response."""
            statement_data = await response.json()
            return {
                "period_ending": statement_data["fundamental"]["end_date"],  # type: ignore
                "fiscal_year": statement_data["fundamental"]["fiscal_year"],  # type: ignore
                "fiscal_period": statement_data["fundamental"]["fiscal_period"],  # type: ignore
                "financials": statement_data["reported_financials"],  # type: ignore
            }

        urls = [
            f"https://api-v2.intrinio.com/fundamentals/{id}/reported_financials?api_key={api_key}"
            for id in ids
        ]

        return await amake_requests(urls, callback, **kwargs)