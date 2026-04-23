async def aextract_data(
        query: SecNportDisclosureQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw data from the SEC endpoint."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        import xmltodict
        from aiohttp_client_cache import SQLiteBackend
        from aiohttp_client_cache.session import CachedSession
        from openbb_core.app.utils import get_user_cache_directory
        from openbb_core.provider.utils.helpers import amake_request
        from openbb_sec.utils.helpers import HEADERS, get_nport_candidates
        from pandas import DataFrame, Series, Timestamp, offsets, to_datetime

        # Implement a retry mechanism in case of RemoteDisconnected Error.
        retries = 3
        for i in range(retries):
            filings = []
            try:
                filings = await get_nport_candidates(
                    symbol=query.symbol, use_cache=query.use_cache
                )
                if filings:
                    break
            except Exception as e:
                if i < retries - 1:
                    warn(f"Error: {e}. Retrying...")
                    await asyncio.sleep(1)
                    continue
                raise e

        filing_candidates = DataFrame.from_records(filings)

        if filing_candidates.empty:
            raise OpenBBError(f"No N-Port records found for {query.symbol}.")

        dates = filing_candidates.period_ending.to_list()
        new_date: str = ""

        if query.year is not None and query.quarter is None:
            query.quarter = 4 if query.year < max(dates).year else 1

        if query.quarter is not None and query.year is not None:
            date = (
                Timestamp(f"{query.year}-Q{query.quarter}") + offsets.QuarterEnd()
            ).date()
            # Gets the URL for the nearest date to the requested date.
            __dates = Series(to_datetime(dates))
            __date = to_datetime(date)
            __nearest = DataFrame(__dates - __date)
            __nearest_date = abs(__nearest[0].astype("int64")).idxmin()
            new_date = __dates[__nearest_date].strftime("%Y-%m-%d")
            date = new_date if new_date else date
            filing_url = filing_candidates[filing_candidates["period_ending"] == date][
                "primary_doc"
            ].values[0]
        else:
            filing_url = filing_candidates["primary_doc"].values[0]

        async def callback(response, session):
            """Response callback for the request."""
            return await response.read()

        response: dict | list[dict] = []
        if query.use_cache is True:
            cache_dir = f"{get_user_cache_directory()}/http/sec_etf"
            async with CachedSession(cache=SQLiteBackend(cache_dir)) as session:
                try:
                    response = await amake_request(
                        filing_url,
                        headers=HEADERS,
                        session=session,
                        response_callback=callback,  # type: ignore
                    )
                finally:
                    await session.close()
        else:
            response = await amake_request(
                filing_url,
                headers=HEADERS,
                response_callback=callback,  # type: ignore
            )
        results = xmltodict.parse(response)  # type: ignore

        return results