async def aextract_data(
        query: CftcCotQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Extract the data from the CFTC API."""
        # pylint: disable=import-outside-toplevel
        import os  # noqa
        from datetime import timedelta
        from openbb_core.provider.utils.helpers import amake_request

        app_token = (
            credentials.get("cftc_app_token")
            if credentials
            else os.getenv("CFTC_APP_TOKEN") or ""
        )

        today = datetime.now()

        _id = "" if query.code == "all" else query.code  # type: ignore
        if _id.startswith("CFTC_"):
            _id = _id[5:]

        is_code = _id and _id[:3].isdigit()
        _start = (
            "1995-01-01"
            if is_code
            else (
                (today - timedelta(days=(today.weekday() - 1) % 7)).strftime("%Y-%m-%d")
            )
        )
        start_date = (
            query.start_date.strftime("%Y-%m-%d") if query.start_date else _start
        )
        end_date = (
            query.end_date.strftime("%Y-%m-%d")
            if query.end_date
            else f"{today.year}-12-31"
        )
        date_range = (
            "$where=Report_Date_as_YYYY_MM_DD"
            f" between '{start_date}' AND '{end_date}'"
        )
        report_type = query.report_type.replace("financial", "tff")

        if query.futures_only is True and report_type != "supplemental":
            report_type += "_futures_only"
        elif query.futures_only is False and report_type != "supplemental":
            report_type += "_combined"

        if not is_code and _id:
            _id = f"%{_id}%"

        _id = _id.replace("+", "%2B").replace("&", "%26")
        base_url = f"https://publicreporting.cftc.gov/resource/{reports_dict[report_type]}.json?$limit=1000000&{date_range}"
        order = "&$order=Report_Date_as_YYYY_MM_DD ASC"
        url = (
            (
                f"{base_url}"
                f" AND (UPPER(contract_market_name) like UPPER('{_id}') "
                f"OR UPPER(commodity) like UPPER('{_id}') "
                f"OR UPPER(cftc_contract_market_code) like UPPER('{_id}') "
                f"OR UPPER(commodity_group_name) like UPPER('{_id}') "
                f"OR UPPER(commodity_subgroup_name) like UPPER('{_id}'))"
            )
            if _id
            else base_url
        )
        url = f"{url}{order}"

        if app_token:
            url += f"&$$app_token={app_token}"

        try:
            response = await amake_request(url, **kwargs)
        except OpenBBError as error:
            raise error from error

        if not response:
            raise EmptyDataError(f"No data found for {_id.replace('%', '')}.")

        return response