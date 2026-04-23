async def aextract_data(
        query: FMPInstitutionalOwnershipQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list:
        """Return the raw data from the FMP endpoint."""
        # pylint: disable=import-outside-toplevel
        from pandas import Timestamp, offsets

        api_key = credentials.get("fmp_api_key") if credentials else ""
        symbols = query.symbol.split(",")
        year = query.year if query.year else None
        quarter = query.quarter if query.quarter else None

        if year is None and quarter is None:
            current = (Timestamp("now") + offsets.QuarterEnd()) - offsets.QuarterEnd()
            quarter = current.quarter
            year = current.year
        elif year is None and quarter is not None:
            year = Timestamp("now").year
        elif year is not None and quarter is None:
            current = Timestamp("now")
            quarter = (
                4
                if year < current.year
                else current.quarter - 1 if current.quarter > 1 else 1
            )

        urls: list[str] = [
            "https://financialmodelingprep.com/stable/institutional-ownership/symbol-positions-summary"
            + f"?symbol={symbol}&year={year}&quarter={quarter}&apikey={api_key}"
            for symbol in symbols
        ]

        return await get_data_urls(urls, **kwargs)