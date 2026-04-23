async def aextract_data(
        query: FMPHistoricalEpsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list:
        """Return the raw data from the FMP endpoint."""
        # pylint: disable=import-outside-toplevel
        import warnings  # noqa
        from openbb_fmp.utils.helpers import get_data_many

        api_key = credentials.get("fmp_api_key") if credentials else ""
        limit = query.limit + 5 if query.limit is not None else 1000
        results: list = []
        symbols = query.symbol.split(",")

        for symbol in symbols:
            url = f"https://financialmodelingprep.com/stable/earnings?symbol={symbol}&limit={limit}&apikey={api_key}"
            result: list = await get_data_many(url, **kwargs)

            if not result:
                warnings.warn(f"No data found for symbol: {symbol}")
                continue

            results.extend(
                [
                    d
                    for d in sorted(result, key=lambda x: x.get("date"), reverse=True)
                    if d.get("epsActual")
                    or d.get("revenueActual")
                    and d.get("date") <= str(dateType.today())
                ][: query.limit if query.limit is not None else None]
            )

        return results