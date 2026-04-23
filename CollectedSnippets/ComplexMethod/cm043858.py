def get_international_portfolio_data(
    index: str | None = None,
    country: str | None = None,
    dividends: bool = True,
) -> str:
    """Download and extract the international index or country portfolio data.

    Note: Not intended for direct use, this function is called by `get_international_portfolio`.
    """
    # pylint: disable=import-outside-toplevel
    import zipfile
    from io import BytesIO

    url: str = ""
    data: str = ""
    if not index and not country:
        raise ValueError("Please provide either an index or a country.")
    if index and country:
        raise ValueError(
            "Please provide either an index or a country, not both at the same time."
        )
    if index:
        index = INTERNATIONAL_INDEX_PORTFOLIO_FILES.get(index)

        if not index:
            raise ValueError(
                f"Index {index} not found in available indexes: "
                + f"{INTERNATIONAL_INDEX_PORTFOLIO_FILES}"
            )
        url = (
            BASE_URL
            + INTERNATIONAL_INDEX_PORTFOLIOS_URLS["dividends" if dividends else "ex"]
        )
    if country:
        country = country.title().replace("_", " ")
        if country not in list(COUNTRY_PORTFOLIO_FILES):
            raise ValueError(
                f"Country {country} not found in available countries: "
                + f"{COUNTRY_PORTFOLIO_FILES}"
            )
        url = BASE_URL + COUNTRY_PORTFOLIOS_URLS["dividends" if dividends else "ex"]
        index = COUNTRY_PORTFOLIO_FILES[country]

    response = download_international_portfolios(url)

    with zipfile.ZipFile(BytesIO(response.content)) as f:
        filenames = f.namelist()

        if index in filenames:
            try:
                with f.open(index) as file:
                    data = file.read().decode("utf-8")
            except UnicodeDecodeError:
                # Fallback to latin-1 encoding if utf-8 fails
                with f.open(index) as file:
                    data = file.read().decode("latin-1")
        else:
            raise ValueError(
                f"Index {index} not found in available indexes: {filenames}"
            )

    return data