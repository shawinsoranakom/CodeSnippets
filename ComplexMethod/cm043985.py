async def aextract_data(
        query: FmpCalendarEventsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list:
        """Extract data from the API."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        import warnings
        from datetime import timedelta
        from openbb_core.provider.utils.errors import EmptyDataError, OpenBBError
        from openbb_fmp.utils.helpers import get_data
        from pandas import date_range, to_datetime

        api_key = credentials.get("fmp_api_key") if credentials else ""

        warnings.warn(
            message="This endpoint appears to be deprecated. Please use the earnings calendar endpoint instead.",
        )
        base_url = (
            "https://financialmodelingprep.com/api/v4/earning-calendar-confirmed?"
        )

        start_date = to_datetime(
            query.start_date if query.start_date else dateType.today()
        )
        end_date = to_datetime(
            query.end_date if query.end_date else (dateType.today() + timedelta(days=3))
        )

        # Assuming limit of 1000 events per request, and peak earnings season
        # with 200+ events per day, in America alone, we split into 3-day ranges.
        # We don't actually know what the API limitations are, so this is a conservative guess.
        date_ranges = date_range(start=start_date, end=end_date, freq="3D")
        if end_date not in date_ranges:
            date_ranges = date_ranges.append(to_datetime([end_date]))

        urls: list = []
        results: list = []

        for i in range(len(date_ranges) - 1):
            from_date = date_ranges[i].strftime("%Y-%m-%d")
            to_date = date_ranges[i + 1].strftime("%Y-%m-%d")
            urls.append(
                f"{base_url}from={from_date}&to={to_date}&limit=1000&apikey={api_key}"
            )

        async def get_one(url):
            """Get data from one URL."""
            try:
                response = await get_data(url, **kwargs)
            except OpenBBError as e:
                raise e from e

            if response:
                results.extend(response)

        await asyncio.gather(*[get_one(url) for url in urls])

        if not results:
            raise EmptyDataError("The request was returned empty.")

        return sorted(results, key=lambda x: x["date"])