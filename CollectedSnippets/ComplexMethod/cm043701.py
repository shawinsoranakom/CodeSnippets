async def bill_text_urls(
    bill_url: str,
    provider: str = "congress_gov",
    is_workspace: bool = False,
) -> list:
    """Get document choices for a specific bill.

    This function is used by the Congressional Bills Viewer widget, in OpenBB Workspace,
    to populate PDF document choices for the selected bill.

    When 'is_workspace' is False (default), it returns a list of the available text versions
    of the specified bill and their download links for the different formats.

    Parameters
    ----------
    bill_url : str
        The base URL of the bill (e.g., "https://api.congress.gov/v3/bill/119/s/1947?format=json").
        This can also be a shortened version like "119/s/1947".
    provider : str
        The provider name, always "congress_gov". This is a dummy parameter.
    is_workspace : bool
        Whether the request is coming from the OpenBB Workspace.
        This alters the output format to conform to the Workspace's expectations.

    Returns
    -------
    list[dict]
        Returns a list of dictionaries with 'label' and 'value' keys, when `is_workspace` is True.
        Otherwise, returns the 'text' object from the Congress.gov API response.
    """
    # pylint: disable=import-outside-toplevel
    from openbb_congress_gov.utils.helpers import get_bill_text_choices

    if not bill_url and is_workspace is True:
        return [
            {
                "label": "Enter a valid bill URL to view available documents.",
                "value": "",
            }
        ]

    if not bill_url:
        raise HTTPException(
            status_code=500,
            detail="Bill URL is required. Please provide a valid bill URL or number.",
        )

    if (bill_url.startswith("/") and bill_url[1].isdigit()) or bill_url[0].isdigit():
        # If the bill_url is a number, assume it is a congress number and append the base URL
        base_url = "https://api.congress.gov/v3/bill"
        bill_url = (
            base_url + bill_url
            if bill_url.startswith("/")
            else (base_url + "/" + bill_url if bill_url[0].isdigit() else bill_url)
        ) + "?format=json"

    return await get_bill_text_choices(bill_url=bill_url, is_workspace=is_workspace)