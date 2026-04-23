async def aextract_data(
        query: FMPEquityOwnershipQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the FMP endpoint."""
        # pylint: disable=import-outside-toplevel
        from openbb_fmp.utils.helpers import get_data_many
        from pandas import Timestamp, offsets

        api_key = credentials.get("fmp_api_key") if credentials else ""

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

        url = (
            "https://financialmodelingprep.com/stable/institutional-ownership/extract-analytics/holder"
            + f"?symbol={query.symbol}&year={year}&quarter={quarter}&page={query.page or 0}"
            + f"&limit={query.limit or 100}&apikey={api_key}"
        )

        return await get_data_many(url, **kwargs)