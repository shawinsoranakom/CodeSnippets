async def aextract_data(
        query: SecCompanyFilingsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Extract the data from the SEC endpoint."""
        # pylint: disable=import-outside-toplevel
        from aiohttp_client_cache import SQLiteBackend
        from aiohttp_client_cache.session import CachedSession
        from openbb_core.app.utils import get_user_cache_directory
        from openbb_core.provider.utils.helpers import amake_request, amake_requests
        from openbb_sec.utils.helpers import symbol_map
        from pandas import DataFrame

        filings = DataFrame()

        if query.symbol and not query.cik:
            query.cik = await symbol_map(
                query.symbol.lower(), use_cache=query.use_cache
            )
            if not query.cik:
                raise OpenBBError(f"CIK not found for symbol {query.symbol}")
        if query.cik is None:
            raise OpenBBError("CIK or symbol must be provided.")

        # The leading 0s need to be inserted but are typically removed from the data to store as an integer.
        if len(query.cik) != 10:  # type: ignore
            cik_: str = ""
            temp = 10 - len(query.cik)  # type: ignore
            for i in range(temp):
                cik_ = cik_ + "0"
            query.cik = cik_ + str(query.cik)  # type: ignore

        url = f"https://data.sec.gov/submissions/CIK{query.cik}.json"
        data: dict | list[dict] = []
        if query.use_cache is True:
            cache_dir = f"{get_user_cache_directory()}/http/sec_company_filings"
            async with CachedSession(
                cache=SQLiteBackend(cache_dir, expire_after=3600 * 24)
            ) as session:
                await session.delete_expired_responses()
                try:
                    data = await amake_request(url, headers=HEADERS, session=session)  # type: ignore
                finally:
                    await session.close()
        else:
            data = await amake_request(url, headers=HEADERS)  # type: ignore

        # This seems to work for the data structure.
        filings = (
            DataFrame.from_records(data["filings"].get("recent")) if "filings" in data else DataFrame()  # type: ignore
        )
        results = filings.to_dict("records")

        # If there are lots of filings, there will be custom pagination.
        if (
            (query.limit and len(filings) >= 1000)
            or query.form_type is not None
            or query.limit == 0
        ):

            async def callback(response, session):
                """Response callback for excess company filings."""
                result = await response.json()
                if result:
                    new_data = DataFrame.from_records(result)
                    results.extend(new_data.to_dict("records"))

            urls: list = []
            new_urls = DataFrame(data["filings"].get("files")) if "filings" in data else DataFrame()  # type: ignore
            for i in new_urls.index:
                new_cik: str = data["filings"]["files"][i]["name"]  # type: ignore
                new_url: str = "https://data.sec.gov/submissions/" + new_cik
                urls.append(new_url)
            if query.use_cache is True:
                cache_dir = f"{get_user_cache_directory()}/http/sec_company_filings"
                async with CachedSession(
                    cache=SQLiteBackend(cache_dir, expire_after=3600 * 24)
                ) as session:
                    try:
                        await amake_requests(urls, headers=HEADERS, session=session, response_callback=callback)  # type: ignore
                    finally:
                        await session.close()
            else:
                await amake_requests(urls, headers=HEADERS, response_callback=callback)  # type: ignore

        return results