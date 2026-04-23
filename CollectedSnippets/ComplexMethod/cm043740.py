async def aextract_data(
        query: SecLatestFinancialReportsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Extract the raw data from the SEC."""
        # pylint: disable=import-outside-toplevel
        from datetime import timedelta  # noqa
        from openbb_core.provider.utils.helpers import amake_request
        from warnings import warn

        today = dateType.today()
        query_date = query.date if query.date is not None else today

        if query_date.weekday() > 4:
            query_date -= timedelta(days=query_date.weekday() - 4)

        date = query_date.strftime("%Y-%m-%d")

        SEARCH_HEADERS = {
            "User-Agent": "my real company name definitelynot@fakecompany.com",
            "Accept-Encoding": "gzip, deflate",
        }

        forms = (
            query.report_type
            if query.report_type is not None
            else (
                "1-K%2C1-SA%2C1-U%2C1-Z%2C1-Z-W%2C10-D%2C10-K%2C10-KT%2C10-Q%2C10-QT%2C11-K%2C11-KT%2C15-12B%2C15-12G%2C"
                "15-15D%2C15F-12B%2C15F-12G%2C15F-15D%2C18-K%2C20-F%2C24F-2NT%2C25%2C25-NSE%2C40-17F2%2C40-17G%2C40-F%2C"
                "6-K%2C8-K%2C8-K12G3%2C8-K15D5%2CABS-15G%2CABS-EE%2CANNLRPT%2CDSTRBRPT%2CN-30B-2%2CN-30D%2CN-CEN%2CN-CSR%2C"
                "N-CSRS%2CN-MFP%2CN-MFP1%2CN-MFP2%2CN-PX%2CN-Q%2CNSAR-A%2CNSAR-B%2CNSAR-U%2CNT%2010-D%2CNT%2010-K%2C"
                "NT%2010-Q%2CNT%2011-K%2CNT%2020-F%2CQRTLYRPT%2CSD%2CSP%2015D2"
            )
        )

        def get_url(date, offset):
            return (
                "https://efts.sec.gov/LATEST/search-index?dateRange=custom"
                f"&category=form-cat1&startdt={date}&enddt={date}&forms={forms}&count=100&from={offset}"
            )

        n_hits = 0
        results: list = []
        url = get_url(date, n_hits)
        try:
            response = await amake_request(url, headers=SEARCH_HEADERS)
        except OpenBBError as e:
            raise OpenBBError(f"Failed to get SEC data: {e}") from e

        if not isinstance(response, dict):
            raise OpenBBError(
                f"Unexpected data response. Expected dictionary, got {response.__class__.__name__}"
            )

        hits = response.get("hits", {})
        total_hits = hits.get("total", {}).get("value")

        if hits.get("hits"):
            results.extend(hits["hits"])

        n_hits += len(results)

        while n_hits < total_hits:
            offset = n_hits
            url = get_url(date, offset)
            try:
                response = await amake_request(url, headers=SEARCH_HEADERS)
            except Exception as e:
                warn(f"Failed to get the next page of SEC data: {e}")
                break

            hits = response.get("hits", {})
            new_results = hits.get("hits", [])

            if not new_results:
                break

            results.extend(new_results)
            n_hits += len(new_results)

        if not results and query.report_type is None:
            raise OpenBBError("No data was returned.")

        if not results and query.report_type is not None:
            raise EmptyDataError(
                f"No data was returned for form type {query.report_type}."
            )

        return results