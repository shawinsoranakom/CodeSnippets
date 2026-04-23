async def committee_document_urls(
    chamber: str,
    committee: str,
    subcommittee: str | None = None,
    doc_type: str = "all",
    congress: int | None = None,
    provider: str = "congress_gov",
    is_workspace: bool = False,
    use_cache: bool = True,
) -> list:
    """Get document choices for a Congressional Committee.

    This endpoint populates the Committee Document Viewer file selector
    with the committee's available documents by type.
    """
    # pylint: disable=import-outside-toplevel
    import datetime
    import re as _re

    from openbb_congress_gov.utils.committees import fetch_committee_documents
    from openbb_congress_gov.utils.helpers import (
        check_api_key,
        year_to_congress,
    )

    if not committee and is_workspace is True:
        return [
            {
                "label": "Select a committee to view available documents.",
                "value": "",
            }
        ]

    if not committee:
        raise HTTPException(
            status_code=500,
            detail="Committee system code is required.",
        )

    api_key = check_api_key()
    system_code = (subcommittee or committee).lower()

    if congress is None:
        congress = year_to_congress(datetime.date.today().year)

    items = await fetch_committee_documents(
        chamber=chamber.lower(),
        system_code=system_code,
        congress=congress,
        doc_type=doc_type,
        api_key=api_key,
        use_cache=use_cache,
    )

    def _clean_label(text: str) -> str:
        text = _re.sub(r"\s*\[TEXT NOT AVAILABLE[^\]]*\]", "", text)
        text = _re.sub(r"\s*\[REFER TO[^\]]*\]", "", text)
        return text.strip()

    _date_re = _re.compile(r"^\[(\d{4}-\d{2}-\d{2})\]\s*")

    choices = []

    for item in items:
        citation = item.get("citation") or ""
        title = _clean_label(item.get("title") or "")
        short_cite = ""

        if citation:
            cite_m = _re.match(
                r"((?:S|H)\.\s*(?:Hrg|Rept|Rpt|Prt|Doc)\.\s*\d{2,3}-\d+(?:,\s*(?:Book|Part)\s*\d+)?)",
                citation,
            )
            if cite_m:
                short_cite = cite_m.group(1)

        date_m = _date_re.match(title)
        date_prefix = ""
        if date_m:
            date_prefix = f"[{date_m.group(1)}] "
            title = title[date_m.end() :]

        if short_cite and title:
            label = f"{date_prefix}{short_cite} — {title}"
        elif title:
            label = f"{date_prefix}{title}"
        elif citation:
            label = date_prefix + _re.sub(r"\s*\(.*?\)\s*$", "", citation).strip()
        else:
            label = date_prefix + item.get("doc_url", "Unknown")

        choices.append({"label": label, "value": item.get("doc_url", "")})

    choices.sort(key=lambda c: c["label"], reverse=True)

    if not choices:
        return [{"label": "No documents found.", "value": ""}]

    return choices