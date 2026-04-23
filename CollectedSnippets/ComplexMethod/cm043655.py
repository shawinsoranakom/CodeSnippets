def validate_params(cls, params):
        """Validate the query parameters."""
        if params.get("start_date") is None:
            # If the symbol is provided, there will be considerably less results.
            # Broad market data needs to be confined to a single date.
            params["start_date"] = (
                dateType.today() - timedelta(days=10)
                if params.get("symbol") is not None
                else dateType.today()
            )

        # Ensure the start date is not on a weekend.
        if params.get("start_date").weekday() > 4:  # type: ignore
            params["start_date"] = params.get("start_date") + timedelta(days=4 - params.get("start_date").weekday())  # type: ignore

        # If the end date is not provided, set it to the start date.
        if params.get("end_date") is None:
            params["end_date"] = params.get("start_date")

        # Ensure the start date is before the end date.
        if params.get("start_date") > params.get("end_date"):  # type: ignore
            params["start_date"], params["end_date"] = (
                params["end_date"],
                params["start_date"],
            )

        # Ensure we are not overloading API.
        if (
            params.get("symbol") is None
            and (params.get("end_date") - params.get("start_date")).days >= 1
        ):
            raise OpenBBError(
                "When no symbol is supplied, queries are not allowed if"
                + " the date range covers more than one trading day."
                + " Supply only the start_date for queries with no symbol."
            )

        # Ensure the end date is not on a weekend.
        if params.get("end_date").weekday() > 4:  # type: ignore
            params["end_date"] = params.get("end_date") + timedelta(days=7 - params.get("end_date").weekday())  # type: ignore

        # Intrinio appears to make the end date not inclusive.
        # It doesn't want the start/end dates to be the same, set the end date to the next day.
        if params.get("end_date") is not None or params.get("start_date") == params.get(
            "end_date"
        ):
            params["end_date"] = params.get("end_date") + timedelta(days=1)  # type: ignore

        return params