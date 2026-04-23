async def aextract_data(
        query: CongressBillTextQueryParams,
        credentials: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list:
        """Extract data from the query."""
        # pylint: disable=import-outside-toplevel
        import base64  # noqa
        from io import BytesIO
        from openbb_core.provider.utils.helpers import make_request

        urls = (
            query.urls.get("urls", [])
            if isinstance(query.urls, dict)
            else (query.urls if isinstance(query.urls, list) else query.urls.split(","))
        )
        results: list = []

        for url in urls:
            from urllib.parse import urlparse

            filename = urlparse(url).path.split("/")[-1]

            _url_lower = url.strip().lower()
            if "congress.gov" not in _url_lower and "govinfo.gov" not in _url_lower:
                results.append(
                    {
                        "error_type": "invalid_url",
                        "content": f"Invalid URL: {url}. Must be a valid Congress.gov or GovInfo URL.",
                        "filename": filename,
                    }
                )
                continue
            try:
                response = make_request(url)
                response.raise_for_status()
                datatype = filename.split(".")[-1].lower()

                if datatype == "pdf":
                    pdf_content = base64.b64encode(
                        BytesIO(response.content).read()
                    ).decode("utf-8")
                    results.append(
                        {
                            "content": pdf_content,
                            "data_format": {
                                "data_type": "pdf",
                                "filename": url.split("/")[-1],
                            },
                        }
                    )
                else:
                    results.append(
                        {
                            "content": response.text,
                            "data_format": {
                                "data_type": "text",
                                "filename": filename,
                            },
                        }
                    )
            except Exception as exc:  # pylint: disable=broad-except
                results.append(
                    {
                        "error_type": "download_error",
                        "content": f"{exc.__class__.__name__}: {exc.args[0]}",
                        "filename": url.split("/")[-1],
                    }
                )
                continue

        return results