async def get_frame(  # pylint: disable=R0912,R0913,R0914,R0915,R0917
    fact: str = "Revenues",
    year: int | None = None,
    fiscal_period: FISCAL_PERIODS | None = None,
    taxonomy: TAXONOMIES | None = "us-gaap",
    units: str | None = "USD",
    instantaneous: bool = False,
    use_cache: bool = True,
) -> dict:
    """Get a frame of data for a given fact.

    Source: https://www.sec.gov/edgar/sec-api-documentation

    The xbrl/frames API aggregates one fact for each reporting entity
    that is last filed that most closely fits the calendrical period requested.

    This API supports for annual, quarterly and instantaneous data:

    https://data.sec.gov/api/xbrl/frames/us-gaap/AccountsPayableCurrent/USD/CY2019Q1I.json

    Where the units of measure specified in the XBRL contains a numerator and a denominator,
    these are separated by “-per-” such as “USD-per-shares”. Note that the default unit in XBRL is “pure”.

    The period format is CY#### for annual data (duration 365 days +/- 30 days),
    CY####Q# for quarterly data (duration 91 days +/- 30 days).

    Because company financial calendars can start and end on any month or day and even change in length from quarter to
    quarter according to the day of the week, the frame data is assembled by the dates that best align with a calendar
    quarter or year. Data users should be mindful different reporting start and end dates for facts contained in a frame.

    Parameters
    ----------
    fact : str
        The fact to retrieve. This should be a valid fact from the SEC taxonomy, in UpperCamelCase.
        Defaults to "Revenues".
        AAPL, MSFT, GOOG, BRK-A all report revenue as, "RevenueFromContractWithCustomerExcludingAssessedTax".
        In previous years, they may have reported as "Revenues".
    year : int, optional
        The year to retrieve the data for. If not provided, the current year is used.
    fiscal_period: Literal["fy", "q1", "q2", "q3", "q4"], optional
        The fiscal period to retrieve the data for. If not provided, the most recent quarter is used.
    taxonomy : Literal["us-gaap", "dei", "ifrs-full", "srt"], optional
        The taxonomy to use. Defaults to "us-gaap".
    units : str, optional
        The units to use. Defaults to "USD". This should be a valid unit from the SEC taxonomy, see the notes above.
        The most common units are "USD", "shares", and "USD-per-shares". EPS and outstanding shares facts will
        automatically set.
    instantaneous: bool
        Whether to retrieve instantaneous data. See the notes above for more information. Defaults to False.
        Some facts are only available as instantaneous data.
        The function will automatically attempt to retrieve the data if the initial fiscal quarter request fails.
    use_cache: bool
        Whether to use cache for the request. Defaults to True.

    Returns
    -------
    Dict:
        Nested dictionary with keys, "metadata" and "data".
        The "metadata" key contains information about the frame.
    """
    # pylint: disable=import-outside-toplevel
    from numpy import nan

    current_date = datetime.now().date()
    quarter = FISCAL_PERIODS_DICT.get(fiscal_period) if fiscal_period else None
    if year is None and quarter is None:
        quarter = (current_date.month - 1) // 3
        year = current_date.year

    if year is None:
        year = current_date.year

    persist = current_date.year == year

    if fact in SHARES_FACTS:
        units = "shares"

    if fact in USD_PER_SHARE_FACTS:
        units = "USD-per-shares"

    url = f"https://data.sec.gov/api/xbrl/frames/{taxonomy}/{fact}/{units}/CY{year}"

    if quarter:
        url = url + f"Q{quarter}"

    if instantaneous:
        url = url + "I"

    url = url + ".json"
    response: dict | list[dict] = {}
    try:
        response = await fetch_data(url, use_cache, persist)
    except Exception as e:  # pylint: disable=W0718
        message = (
            "No frame was found with the combination of parameters supplied."
            + " Try adjusting the period."
            + " Not all GAAP measures have frames available."
        )
        if url.endswith("I.json"):
            warn("No instantaneous frame was found, trying calendar period data.")
            url = url.replace("I.json", ".json")
            try:
                response = await fetch_data(url, use_cache, persist)
            except Exception:
                raise OpenBBError(message) from e
        elif "Q" in url and not url.endswith("I.json"):
            warn(
                "No frame was found for the requested quarter, trying instantaneous data."
            )
            url = url.replace(".json", "I.json")
            try:
                response = await fetch_data(url, use_cache, persist)
            except Exception:
                raise OpenBBError(message) from e
        else:
            raise OpenBBError(message) from e

    data = sorted(response.get("data", {}), key=lambda x: x["val"], reverse=True)  # type: ignore
    metadata = {
        "frame": response.get("ccp", ""),  # type: ignore
        "tag": response.get("tag", ""),  # type: ignore
        "label": response.get("label", ""),  # type: ignore
        "description": response.get("description", ""),  # type: ignore
        "taxonomy": response.get("taxonomy", ""),  # type: ignore
        "unit": response.get("uom", ""),  # type: ignore
        "count": response.get("pts", ""),  # type: ignore
    }
    df = DataFrame(data)
    companies = await get_all_companies(use_cache=use_cache)
    cik_to_symbol = companies.set_index("cik")["symbol"].to_dict()
    df["symbol"] = df["cik"].astype(str).map(cik_to_symbol)
    df["unit"] = metadata.get("unit")
    df["fact"] = metadata.get("label")
    df["frame"] = metadata.get("frame")
    df = df.replace({nan: None})
    results = {"metadata": metadata, "data": df.to_dict("records")}

    return results