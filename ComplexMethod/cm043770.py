async def get_nport_candidates(symbol: str, use_cache: bool = True) -> list[dict]:
    """Get a list of all NPORT-P filings for a given fund's symbol."""
    results = []
    _series_id = await get_series_id(symbol, use_cache=use_cache)
    try:
        series_id = (
            await symbol_map(symbol, use_cache)
            if _series_id is None or len(_series_id) == 0
            else _series_id["seriesId"].iloc[0]
        )
    except IndexError as e:
        raise OpenBBError("Fund not found for, the symbol: " + symbol) from e
    if series_id == "" or series_id is None:
        raise OpenBBError("Fund not found for, the symbol: " + symbol)

    url = f"https://efts.sec.gov/LATEST/search-index?q={series_id}&dateRange=all&forms=NPORT-P"
    response: dict | list[dict] = {}
    if use_cache is True:
        cache_dir = f"{get_user_cache_directory()}/http/sec_etf"
        async with CachedSession(cache=SQLiteBackend(cache_dir)) as session:
            try:
                await session.delete_expired_responses()
                response = await amake_request(url, session=session, headers=HEADERS, response_callback=sec_callback)  # type: ignore
            finally:
                await session.close()
    else:
        response = await amake_request(url, response_callback=sec_callback)  # type: ignore

    if "hits" in response and len(response["hits"].get("hits")) > 0:  # type: ignore
        hits = response["hits"]["hits"]  # type: ignore
        results = [
            {
                "name": d["_source"]["display_names"][0],
                "cik": d["_source"]["ciks"][0],
                "file_date": d["_source"]["file_date"],
                "period_ending": d["_source"]["period_ending"],
                "form_type": d["_source"]["form"],
                "primary_doc": (
                    f"https://www.sec.gov/Archives/edgar/data/{int(d['_source']['ciks'][0])}"  # noqa
                    + f"/{d['_id'].replace('-', '').replace(':', '/')}"  # noqa
                ),
            }
            for d in hits
        ]
    return (
        sorted(results, key=lambda d: d["file_date"], reverse=True)
        if len(results) > 0
        else results
    )