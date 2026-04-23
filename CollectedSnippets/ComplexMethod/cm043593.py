async def fomc_documents_download(params: Annotated[dict, Body()]) -> list:
    """Download FOMC documents from the Federal Reserve's website.

    PDFs are base64 encoded under the `content` key in the response.

    Parameters
    ----------
    params : dict
        A dictionary with a key "url" containing a list of URLs to download.

    Returns
    -------
    list
        A list of dictionaries, each containing keys `filename`, `content`, and `data_format`.
    """
    # pylint: disable=import-outside-toplevel
    import base64  # noqa
    from io import BytesIO
    from urllib.parse import urlparse
    from openbb_core.provider.utils.helpers import make_request

    urls = params.get("url", [])
    results: list = []

    for url in urls:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname or ""

        if parsed_url.scheme != "https" or hostname not in {
            "www.federalreserve.gov",
            "federalreserve.gov",
        }:
            raise OpenBBError(
                "Invalid URL provided for download. Must be from federalreserve.gov -> "
                + url
            )

        is_pdf = url.lower().endswith(".pdf")

        if (
            not is_pdf
            and not url.lower().endswith(".htm")
            and not url.lower().endswith(".html")
        ):
            raise OpenBBError(
                "Unsupported document format. File must be PDF or HTM type -> " + url
            )

        try:
            response = make_request(url)
            response.raise_for_status()
            pdf = (
                base64.b64encode(BytesIO(response.content).getvalue()).decode("utf-8")
                if isinstance(response.content, bytes)
                else response.content
            )
            results.append(
                {
                    "content": pdf,
                    "data_format": {
                        "data_type": "pdf" if is_pdf else "markdown",
                        "filename": url.split("/")[-1],
                    },
                }
            )
        except Exception as exc:
            results.append(
                {
                    "error_type": "download_error",
                    "content": f"{exc.__class__.__name__}: {exc.args[0]}",
                    "filename": url.split("/")[-1],
                }
            )
            continue

    return results