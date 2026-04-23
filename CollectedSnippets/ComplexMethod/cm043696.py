async def aextract_data(
        query: CongressBillsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list:
        """Extract data from the Congress API."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import UnauthorizedError  # noqa
        from openbb_core.provider.utils.helpers import amake_request
        from openbb_congress_gov.utils.helpers import (
            get_all_bills_by_type,
        )

        api_key = credentials.get("congress_gov_api_key") if credentials else ""

        # Add congress number and bill type to the path parameters where required.
        # If a bill_type is provided, we need to give the path a congress number.
        # If no congress number is provided, we will use the current congress number
        # or the congress number derived from the start or end date, when supplied.

        if (
            query.bill_type is not None
            and query.start_date is None
            and query.end_date is None
            and query.congress is None
        ):
            congress = year_to_congress(datetime.now().year)
        elif (
            query.bill_type is not None
            and query.congress is None
            and query.start_date is not None
        ):
            congress = year_to_congress(query.start_date.year)
        elif (
            query.bill_type is not None
            and query.congress is None
            and query.end_date is not None
            and query.start_date is None
        ):
            congress = year_to_congress(query.end_date.year)
        elif (
            query.bill_type is not None
            and query.start_date is not None
            and query.end_date is not None
            and query.congress is None
        ):
            congress_start = year_to_congress(query.start_date.year)
            congress = congress_start
        elif query.bill_type is not None and query.congress is None:
            congress = year_to_congress(datetime.now().year)
        else:
            congress = query.congress

        if query.limit == 0 and query.bill_type is not None and congress is not None:
            # If limit is 0, we fetch all bills of the specified type for the congress
            return await get_all_bills_by_type(
                bill_type=query.bill_type,
                congress=congress,
                start_date=None,
                end_date=None,
            )
        url = (
            (
                f"{base_url}bill/{congress}/{query.bill_type}"
                if congress is not None and query.bill_type is not None
                else (
                    f"{base_url}bill/{congress}"
                    if congress is not None
                    else f"{base_url}bill"
                )
            )
            + (
                f"?fromDateTime={query.start_date.strftime('%Y-%m-%d') + 'T00:00:00Z'}"
                if query.start_date
                else ""
            )
            + (
                f"&toDateTime={query.end_date.strftime('%Y-%m-%d') + 'T23:59:59Z'}"
                if query.end_date
                else ""
            )
        )
        url += (
            f"{'?' if '?' not in url else '&'}"
            + f"limit={query.limit if query.limit is not None else '100'}"
            + (f"&offset={query.offset if query.offset else '0'}")
            + f"&sort=updateDate+{query.sort_by}"
            + f"&format=json&api_key={api_key}"
        )

        try:
            response = await amake_request(url=url)
            if isinstance(response, dict) and (error := response.get("error", {})):
                if "API_KEY" in error.get("code", ""):
                    raise UnauthorizedError(
                        f"{error.get('code', '')} -> {error.get('message', '')}"
                    )
                raise OpenBBError(
                    f"{error.get('code', '')} -> {error.get('message', '')}"
                )

        except Exception as e:
            # Handle exceptions
            raise OpenBBError(e) from e

        return response.get("bills", [])