async def get_bills_by_type(
    congress: int | None = None,
    bill_type: str = "hr",
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int | None = None,
    offset: int | None = 0,
    sort_by: Literal["asc", "desc"] = "desc",
) -> dict | list:
    """Fetch bills of a specific type for a given Congress number.

    Results are sorted by date of the latest action on the bill.

    Parameters
    ----------
    congress : Optional[int]
        The Congress number (e.g., 118 for the 118th Congress).
        If None, defaults to the current Congress based on the current year.
    bill_type : str
        The type of bill to fetch (e.g., "hr" for House bills).
    start_date : Optional[str]
        The start date in ISO format (YYYY-MM-DD) for filtering bills.
        If None, no start date filter is applied.
    end_date : Optional[str]
        The end date in ISO format (YYYY-MM-DD) for filtering bills.
        If None, no end date filter is applied.
    limit : Optional[int]
        The maximum number of bills to return. Defaults to 10 if None.
        To fetch all bills, use `get_all_bills_by_type()` instead.
    offset : Optional[int]
        The number of results to skip before starting to collect the result set.
        Defaults to 0 if None.
    sort_by : Literal["asc", "desc"]
        The sort order for the results. Defaults to "desc".

    Returns
    -------
    dict
        A dictionary of the raw JSON response from the API.
    """
    # pylint: disable=import-outside-toplevel
    from datetime import (  # noqa
        date as dateType,
        datetime,
    )
    from openbb_core.provider.utils.helpers import amake_request

    if bill_type and bill_type not in BillTypes:
        raise ValueError(
            f"Invalid bill type: {bill_type}. Must be one of {', '.join(BillTypes)}."
        )

    api_key = check_api_key()

    if start_date is None and end_date is None and congress is None:
        congress = year_to_congress(datetime.now().year)
    elif congress is None and start_date is not None:
        congress = year_to_congress(dateType.fromisoformat(start_date).year)
    elif congress is None and end_date is not None and start_date is None:
        congress = year_to_congress(dateType.fromisoformat(end_date).year)
    elif start_date is not None and end_date is not None:
        start_year = dateType.fromisoformat(start_date).year
        end_year = dateType.fromisoformat(end_date).year
        congress_start = year_to_congress(start_year)
        congress_end = year_to_congress(end_year)
        if congress_start != congress_end:
            raise ValueError(
                "Start and end dates must be in the same Congress session."
            )
        congress = congress_start

    if congress is None:
        congress = year_to_congress(datetime.now().year)

    url = (
        f"{base_url}bill/{congress}/{bill_type}"
        + (f"?fromDateTime={start_date + 'T00:00:00Z'}" if start_date else "")
        + (f"&toDateTime={end_date + 'T23:59:59Z'}" if end_date else "")
        + f"?limit={limit if limit is not None else 10}"
        + (f"&offset={offset}" if offset else "")
        + f"&sort=updateDate+{sort_by}"
        + f"&format=json&api_key={api_key}"
    )

    return await amake_request(url)