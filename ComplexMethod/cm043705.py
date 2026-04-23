async def get_bill_text_choices(bill_url: str, is_workspace: bool = False) -> list:
    """Fetch the direct download links for the available text versions of the specified bill.

    This function is used by the Congressional Bills Viewer widget,
    in OpenBB Workspace, to populate the document choices
    for the selected bill. When `is_workspace` is True,
    it returns a list of dictionaries with 'label' and 'value' keys.

    Parameters
    ----------
    bill_url : str
        The base URL of the bill (e.g., "https://api.congress.gov/v3/bill/119/s/1947?format=json").

    Returns
    -------
    list[dict]
        List of dictionaries with the results.
    """
    # pylint: disable=import-outside-toplevel
    from openbb_core.provider.utils.helpers import amake_request

    api_key = check_api_key()
    results: list = []
    url = bill_url.replace("?", "/text?") + f"&api_key={api_key}"
    response = await amake_request(url)
    bill_text = response.get("textVersions", [])  # type: ignore

    # Return the results for non-Workspace queries
    if is_workspace is False:
        if not bill_text:
            raise HTTPException(
                status_code=404,
                detail="No text available for this bill currently.",
            )

        text_output: list = []
        seen_urls: set = set()

        for version in bill_text:
            bill_version: dict = {}
            formats = version.get("formats", [])
            bill_type = version.get("type", "")
            version_date = version.get("date", "")

            if not formats or not version_date:
                continue

            pdf_url = next(
                (f.get("url") for f in formats if f.get("type") == "PDF"), None
            )

            if pdf_url and pdf_url in seen_urls:
                continue

            if pdf_url:
                seen_urls.add(pdf_url)

            bill_version["version_type"] = bill_type
            bill_version["version_date"] = version_date

            for fmt in formats:
                doc_url = fmt.get("url")
                doc_type = fmt.get("type", "").replace("Formatted ", "").lower()
                bill_version[doc_type] = doc_url

            if bill_version:
                text_output.append(bill_version)

        return text_output

    if not bill_text:
        return [
            {
                "label": "No text available for this bill currently.",
                "value": "",
            }
        ]

    seen_urls = set()

    for version in bill_text:
        version_date = version.get("date")
        formats = version.get("formats", [])
        version_type = version.get("type", "")

        for fmt in formats:
            if (doc_type := fmt.get("type")) and doc_type == "PDF":
                doc_url = fmt.get("url")

                if doc_url in seen_urls:
                    break

                seen_urls.add(doc_url)
                doc_name = doc_url.split("/")[-1]
                filename = (
                    f"{version_type} - {version_date} - {doc_name}"
                    if version_date
                    else doc_name
                )
                results.append(
                    {
                        "label": filename,
                        "value": doc_url,
                    }
                )
                break

    return results