def get_current_fomc_documents(url: str | None = None) -> list:
    """
    Get the current FOMC documents from https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm.

    Returns
    -------
    list
        A list of dictionaries containing the FOMC documents.
        Each dictionary contains the following:
        - date: str
            The date of the document, formatted as YYYY-MM-DD.
        - doc_type: str
            The type of the document.
        - doc_format: str
            The format of the document.
        - url: str
            The URL of the document
    """
    # pylint: disable=import-outside-toplevel
    import re  # noqa
    from bs4 import BeautifulSoup
    from openbb_core.provider.utils.helpers import make_request

    data_releases: list = []
    if url is None:
        beige_books = get_beige_books()

        if beige_books:
            data_releases.extend(beige_books)

    url = (
        url
        if url is not None
        else "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
    )
    response = make_request(url, method="GET")
    soup = BeautifulSoup(response.content, "html.parser")

    for link in soup.find_all("a"):
        url = link.get("href", "")  # type: ignore[assignment]

        if "/newsevents/pressreleases" in url:
            continue

        file_url = (
            f"https://www.federalreserve.gov{url}"
            if not url.startswith("https://www.federalreserve.gov")
            else url
        )
        date = file_url.split("/")[
            -2 if file_url.endswith("/default.htm") else -1
        ].split(".")[0]
        date_match = re.search(r"(\d{4})(\d{2})(\d{2})", date)
        if date_match:
            new_date = (
                f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
            )
            file_type = ""
            if "beige" in url.lower():
                file_type = "beige_book"
            if "files" in url and "monetary" in date:
                file_type = "monetary_policy"
            if "fomcproj" in date:
                file_type = "projections"
            if "fomcminutes" in date:
                file_type = "minutes"
            if "fomcpresconf" in date:
                file_type = "press_conference"

            file_format = file_url.rsplit(".", maxsplit=1)[-1]
            data_releases.append(
                {
                    "date": new_date,
                    "doc_type": file_type,
                    "doc_format": file_format,
                    "url": file_url,
                }
            )

    data_releases = sorted(data_releases, key=lambda x: x["date"], reverse=True)

    return data_releases