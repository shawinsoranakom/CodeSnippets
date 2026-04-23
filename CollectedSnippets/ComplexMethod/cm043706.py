async def get_amendments(
    congress: int | None = None,
    amendment_type: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
    sort_by: Literal["asc", "desc"] = "desc",
) -> dict:
    """Fetch amendments with optional filters.

    Parameters
    ----------
    congress : Optional[int]
        The Congress number. If None, returns amendments across congresses.
    amendment_type : Optional[str]
        The type of amendment. Must be one of: "hamdt", "samdt", "suamdt".
    start_date : Optional[str]
        The start date in ISO format (YYYY-MM-DD) for filtering by updateDate.
    end_date : Optional[str]
        The end date in ISO format (YYYY-MM-DD) for filtering by updateDate.
    limit : Optional[int]
        The maximum number of amendments to return. Defaults to 100 if None.
    offset : Optional[int]
        The number of results to skip before starting to collect the result set.
    sort_by : Literal["asc", "desc"]
        The sort order for the results. Defaults to "desc".

    Returns
    -------
    dict
        A dictionary of the raw JSON response from the API.
    """
    # pylint: disable=import-outside-toplevel
    from openbb_core.provider.utils.helpers import amake_request

    if amendment_type is not None and amendment_type not in AmendmentTypes:
        raise ValueError(
            f"Invalid amendment type: {amendment_type}. Must be one of {', '.join(AmendmentTypes)}."
        )

    api_key = check_api_key()
    url = f"{base_url}amendment"

    if congress is not None:
        url += f"/{congress}"

        if amendment_type is not None:
            url += f"/{amendment_type}"

    url += (f"?fromDateTime={start_date + 'T00:00:00Z'}" if start_date else "") + (
        f"&toDateTime={end_date + 'T23:59:59Z'}" if end_date else ""
    )
    url += (
        f"{'?' if '?' not in url else '&'}"
        + f"limit={limit if limit is not None else 100}"
        + (f"&offset={offset}" if offset else "")
        + f"&sort=updateDate+{sort_by}"
        + f"&format=json&api_key={api_key}"
    )

    return await amake_request(url)