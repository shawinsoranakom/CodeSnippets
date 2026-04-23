async def get_bill_choices(
    congress: int | None = None,
    bill_type: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    bill_url: str | None = None,
    is_document_choices: bool | None = None,
) -> list:
    """Fetch a list of bills of a specific type for a given Congress number.

    This function is not intended to be used directly.

    It is used by the OpenBB Workspace Congressional Bills Viewer widget
    to populate dynamic parameter choices based on the widget's state.
    """
    # pylint: disable=import-outside-toplevel
    from datetime import datetime

    bills_state = BillsState()

    if bill_type and bill_type not in [option["value"] for option in bill_type_options]:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid bill type: {bill_type}."
            + f" Must be one of {', '.join([option['value'] for option in bill_type_options])}.",
        )

    if bill_url:
        return await get_bill_text_choices(bill_url=bill_url)

    if is_document_choices is True and not bill_url:
        return [
            {
                "label": "Select a bill to view associated text.",
                "value": "",
            }
        ]

    if not bill_type:
        bill_type = "hr"

    if not congress:
        congress = year_to_congress(datetime.now().year)

    cached_bills = bills_state.bills.get(f"{congress}_{bill_type}")

    if not cached_bills:
        bills = await get_all_bills_by_type(
            congress=congress,
            bill_type=bill_type,  # type: ignore
        )
        bills_state.bills[f"{congress}_{bill_type}"] = bills
    else:
        bills = cached_bills

    if start_date:
        bills = (
            [bill for bill in bills if bill["latestAction"]["actionDate"] >= start_date]
            if not end_date
            else [
                bill
                for bill in bills
                if bill["latestAction"]["actionDate"] >= start_date
                and bill["latestAction"]["actionDate"] <= end_date
            ]
        )
    elif end_date and not start_date:
        bills = [
            bill for bill in bills if bill["latestAction"]["actionDate"] <= end_date
        ]

    results: list = []

    for bill in sorted(
        bills, key=lambda x: x["latestAction"]["actionDate"], reverse=True
    ):
        bill_title = bill.get("title", "")

        if not bill_title:
            continue

        bill_url = bill.get("url", "")
        label = (
            bill_title
            + f" ({bill.get('number', '')} - {bill['latestAction']['actionDate']})"
        )
        results.append(
            {
                "label": label,
                "value": bill_url,
            }
        )

    return results