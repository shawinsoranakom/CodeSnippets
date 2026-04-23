async def get_concept(
    symbol: str,
    fact: str = "Revenues",
    year: int | None = None,
    taxonomy: TAXONOMIES | None = "us-gaap",
    use_cache: bool = True,
) -> dict:
    """Return all the XBRL disclosures from a single company (CIK) Concept (a taxonomy and tag) into a single JSON file.

    Each entry contains a separate array of facts for each units of measure that the company has chosen to disclose
    (e.g. net profits reported in U.S. dollars and in Canadian dollars).

    Parameters
    ----------
    symbol: str
        The ticker symbol to look up.
    fact : str
        The fact to retrieve. This should be a valid fact from the SEC taxonomy, in UpperCamelCase.
        Defaults to "Revenues".
        AAPL, MSFT, GOOG, BRK-A all report revenue as, "RevenueFromContractWithCustomerExcludingAssessedTax".
        In previous years, they may have reported as "Revenues".
    year : int, optional
        The year to retrieve the data for. If not provided, all reported values will be returned.
    taxonomy : Literal["us-gaap", "dei", "ifrs-full", "srt"], optional
        The taxonomy to use. Defaults to "us-gaap".
    use_cache: bool
        Whether to use cache for the request. Defaults to True.

    Returns
    -------
    Dict:
        Nested dictionary with keys, "metadata" and "data".
        The "metadata" key contains information about the company concept.
    """
    symbols = symbol.split(",")
    results: list[dict] = []
    messages: list = []
    metadata: dict = {}

    async def get_one(ticker):
        """Get data for one symbol."""
        ticker = ticker.upper()
        message = f"Symbol Error: No data was found for, {ticker} and {fact}"
        cik = await symbol_map(ticker)
        if cik == "":
            message = f"Symbol Error: No CIK was found for, {ticker}"
            warn(message)
            messages.append(message)
        else:
            url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/{taxonomy}/{fact}.json"
            response: dict | list[dict] = {}
            try:
                response = await fetch_data(url, use_cache, False)
            except Exception as _:  # pylint: disable=W0718
                warn(message)
                messages.append(message)
            if response:
                units = response.get("units", {})  # type: ignore
                metadata[ticker] = {
                    "cik": response.get("cik", ""),  # type: ignore
                    "taxonomy": response.get("taxonomy", ""),  # type: ignore
                    "tag": response.get("tag", ""),  # type: ignore
                    "label": response.get("label", ""),  # type: ignore
                    "description": response.get("description", ""),  # type: ignore
                    "name": response.get("entityName", ""),  # type: ignore
                    "units": (
                        list(units) if units and len(units) > 1 else list(units)[0]
                    ),
                }
                for k, v in units.items():
                    unit = k
                    values = v
                    for item in values:
                        item["unit"] = unit
                        item["symbol"] = ticker
                        item["cik"] = metadata[ticker]["cik"]
                        item["name"] = metadata[ticker]["name"]
                        item["fact"] = metadata[ticker]["label"]
                    results.extend(values)

    await asyncio.gather(*[get_one(ticker) for ticker in symbols])

    if not results:
        raise EmptyDataError(f"{messages}")

    if year is not None:
        filtered_results = [d for d in results if str(year) == str(d.get("fy"))]
        if len(filtered_results) > 0:
            results = filtered_results
        if len(filtered_results) == 0:
            warn(
                f"No results were found for {fact} in the year, {year}."
                " Returning all entries instead. Concept and fact names may differ by company and year."
            )

    return {
        "metadata": metadata,
        "data": sorted(results, key=lambda x: (x["filed"], x["end"]), reverse=True),
    }