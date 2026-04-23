async def get_13f_candidates(symbol: str | None = None, cik: str | None = None):
    """Get the 13F-HR filings for a given symbol or CIK."""
    # pylint: disable=import-outside-toplevel
    from openbb_sec.models.company_filings import SecCompanyFilingsFetcher
    from pandas import DataFrame, to_datetime

    fetcher = SecCompanyFilingsFetcher()
    params: dict[str, Any] = {}
    if cik is not None:
        params["cik"] = str(cik)
    if symbol is not None:
        params["symbol"] = symbol
    if cik is None and symbol is None:
        raise OpenBBError("Either symbol or cik must be provided.")

    params["use_cache"] = False
    params["form_type"] = "13F-HR"
    filings = await fetcher.fetch_data(params, {})
    filings = [d.model_dump() for d in filings]  # type: ignore
    if len(filings) == 0:
        raise OpenBBError(f"No 13F-HR filings found for {symbol if symbol else cik}.")

    # Filings before June 30, 2013 are non-structured and are not supported by downstream parsers.
    up_to = to_datetime("2013-06-30").date()  # pylint: disable=unused-variable # noqa
    return (
        DataFrame(data=filings)
        .query("`report_date` >= @up_to")
        .set_index("report_date")["complete_submission_url"]
        .fillna("N/A")
        .replace("N/A", None)
    )