async def get_amendment_text_choices(  # noqa: PLR0912
    amendment_url: str, is_workspace: bool = False
) -> list:
    """Fetch the direct download links for the available text versions of the specified amendment.

    Makes multiple API calls:
    1. GET the amendment base detail to retrieve the official textVersions URL and description.
    2. GET the textVersions sub-resource via the URL returned in the detail response.
    3. If the description references a committee report (e.g., "House Report 119-1"),
       GET that report's text — these documents contain the clean printed amendment text
       and are returned first (higher priority than Congressional Record references).

    Parameters
    ----------
    amendment_url : str
        The base URL of the amendment
        (e.g., "https://api.congress.gov/v3/amendment/119/hamdt/2?format=json")
        or a shorthand like "119/hamdt/2".
    is_workspace : bool
        When True, returns {label, value} dicts suitable for workspace dropdowns.

    Returns
    -------
    list
        List of dictionaries with available text version formats.
    """
    # pylint: disable=import-outside-toplevel
    import re

    from openbb_core.provider.utils.helpers import amake_request

    api_key = check_api_key()

    if amendment_url[0].isnumeric() or (
        amendment_url[0] == "/" and amendment_url[1].isnumeric()
    ):
        path = amendment_url[1:] if amendment_url[0] == "/" else amendment_url
        amendment_url = f"https://api.congress.gov/v3/amendment/{path}?format=json"

    # Step 1: Amendment base detail for description (committee report check) and text URL
    detail_response: dict = await amake_request(amendment_url + f"&api_key={api_key}")  # type: ignore
    amendment_detail = detail_response.get("amendment", {})

    # Step 2: Fetch the /text sub-resource.
    tv_info = amendment_detail.get("textVersions", {})

    if isinstance(tv_info, dict) and tv_info.get("url"):
        tv_url = tv_info["url"] + f"&api_key={api_key}"
    else:
        # Construct the /text URL directly as a fallback
        tv_url = amendment_url.replace("?", "/text?") + f"&api_key={api_key}"

    tv_response: dict = await amake_request(tv_url)  # type: ignore
    text_versions: list = tv_response.get("textVersions", [])
    # Step 3: Check if the amendment was printed in a committee report and fetch that text
    committee_report_text: list = []
    description = (
        amendment_detail.get("description") or amendment_detail.get("purpose") or ""
    )
    report_match = re.search(
        r"\b(House|Senate)\s+Report\s+(\d+)-(\d+)", description, re.IGNORECASE
    )

    if report_match:
        report_congress = report_match.group(2)
        report_number = report_match.group(3)
        report_type = "hrpt" if report_match.group(1).lower() == "house" else "srpt"
        report_text_url = (
            f"https://api.congress.gov/v3/committeeReport/{report_congress}"
            f"/{report_type}/{report_number}/text?format=json&api_key={api_key}"
        )
        try:
            report_response: dict = await amake_request(report_text_url)  # type: ignore
            if isinstance(report_response, dict) and "text" in report_response:
                committee_report_text = report_response.get("text", [])
        except Exception:  # pylint: disable=broad-except  # noqa: S110
            pass

    # Step 4: If no text versions found, fall back to the amended bill's text versions.
    bill_text_versions: list = []

    if not text_versions and not committee_report_text:
        amended_bill = amendment_detail.get("amendedBill", {})
        bill_url = amended_bill.get("url", "") if amended_bill else ""

        if bill_url:
            bill_text_url = bill_url.replace("?", "/text?") + f"&api_key={api_key}"

            try:
                bill_tv_response: dict = await amake_request(bill_text_url)  # type: ignore
                bill_text_versions = bill_tv_response.get("textVersions", [])
            except Exception:  # pylint: disable=broad-except  # noqa: S110
                pass

    if is_workspace is False:
        if not text_versions and not committee_report_text and not bill_text_versions:
            raise HTTPException(
                status_code=404,
                detail="No text available for this amendment currently.",
            )

        text_output: list = []
        seen_pdf_urls: set = set()

        def _deduped_entry(entry: dict, formats: list) -> dict | None:
            pdf_url = next(
                (f.get("url") for f in formats if f.get("type") == "PDF"), None
            )

            if pdf_url and pdf_url in seen_pdf_urls:
                return None

            if pdf_url:
                seen_pdf_urls.add(pdf_url)

            for fmt in formats:
                doc_url = fmt.get("url")
                doc_type = fmt.get("type", "").replace("Formatted ", "").lower()
                entry[doc_type] = doc_url

            return entry

        for version in committee_report_text:
            formats = version.get("formats", [])
            entry: dict = {
                "version_type": "Committee Report",
                "version_date": version.get("date", ""),
            }
            result = _deduped_entry(entry, formats)

            if result:
                text_output.append(result)

        for version in text_versions:
            formats = version.get("formats", [])
            version_type = version.get("type", "")
            version_date = version.get("date", "")

            if not formats or not version_date:
                continue

            entry = {"version_type": version_type, "version_date": version_date}
            result = _deduped_entry(entry, formats)

            if result:
                text_output.append(result)

        for version in bill_text_versions:
            formats = version.get("formats", [])
            version_type = version.get("type", "")
            version_date = version.get("date", "")

            if not formats or not version_date:
                continue

            entry = {
                "version_type": f"Bill Text - {version_type}",
                "version_date": version_date,
            }
            result = _deduped_entry(entry, formats)

            if result:
                text_output.append(result)

        return text_output

    if not text_versions and not committee_report_text and not bill_text_versions:
        return [
            {"label": "No text available for this amendment currently.", "value": ""}
        ]

    results: list = []

    # Committee report documents first — these are the printed amendment text
    for version in committee_report_text:
        version_date = version.get("date", "")
        for fmt in version.get("formats", []):
            if fmt.get("type") == "PDF":
                doc_url = fmt.get("url", "")
                doc_name = doc_url.split("/")[-1]
                label = (
                    f"Committee Report - {version_date} - {doc_name}"
                    if version_date
                    else doc_name
                )
                results.append({"label": label, "value": doc_url})
                break

    seen_urls_ws: set = set()

    # Congressional Record / other text versions
    for version in text_versions:
        version_date = version.get("date")
        formats = version.get("formats", [])
        version_type = version.get("type", "")

        for fmt in formats:
            if (doc_type := fmt.get("type")) and doc_type == "PDF":
                doc_url = fmt.get("url", "")

                if doc_url in seen_urls_ws:
                    break

                seen_urls_ws.add(doc_url)
                doc_name = doc_url.split("/")[-1]
                filename = (
                    f"{version_type} - {version_date} - {doc_name}"
                    if version_date
                    else doc_name
                )
                results.append({"label": filename, "value": doc_url})
                break

    # Amended bill text fallback (for ANS amendments that adopt the printed bill)
    for version in bill_text_versions:
        version_date = version.get("date")
        formats = version.get("formats", [])
        version_type = version.get("type", "")

        for fmt in formats:
            if (doc_type := fmt.get("type")) and doc_type == "PDF":
                doc_url = fmt.get("url", "")

                if doc_url in seen_urls_ws:
                    break

                seen_urls_ws.add(doc_url)
                doc_name = doc_url.split("/")[-1]
                filename = (
                    f"Bill Text ({version_type}) - {version_date} - {doc_name}"
                    if version_date
                    else doc_name
                )
                results.append({"label": filename, "value": doc_url})
                break

    return results