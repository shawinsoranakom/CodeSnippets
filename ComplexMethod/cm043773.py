async def get_form_4_urls(
    symbol,
    start_date: dateType | None = None,
    end_date: dateType | None = None,
    use_cache: bool = True,
):
    """Get the form 4 URLs for a symbol."""
    # pylint: disable=import-outside-toplevel
    from openbb_sec.models.company_filings import SecCompanyFilingsFetcher

    fetcher = SecCompanyFilingsFetcher()
    form_4 = await fetcher.fetch_data(
        dict(
            symbol=symbol,
            form_type="4",
            provider="sec",
            limit=0,
            use_cache=use_cache,
        ),
        {},
    )
    start_date = (
        start_date
        if isinstance(start_date, dateType)
        else (dateType.fromisoformat(start_date) if start_date and isinstance(start_date, str) else None)  # type: ignore
    )
    end_date = (
        end_date
        if isinstance(end_date, dateType)
        else (dateType.fromisoformat(end_date) if end_date and isinstance(end_date, str) else None)  # type: ignore
    )
    urls: list = []
    for item in form_4:
        if (
            (not start_date or not item.filing_date)  # type: ignore
            or start_date
            and item.filing_date < start_date  # type: ignore
        ):
            continue
        if (
            (not end_date or not item.report_date)  # type: ignore
            or end_date
            and item.report_date > end_date  # type: ignore
        ):
            continue
        to_replace = f"{item.primary_doc.split('/')[0]}/"  # type: ignore
        form_url = item.report_url.replace(to_replace, "")  # type: ignore
        if form_url.endswith(".xml"):
            urls.append(form_url)

    return urls