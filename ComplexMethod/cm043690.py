async def get_intraday_price_history(
    symbol: str,
    start_date: str | dateType | None = None,
    end_date: str | dateType | None = None,
    interval: int | None = 1,
):
    """Get historical price data."""
    # pylint: disable=import-outside-toplevel
    import json  # noqa
    import asyncio  # noqa
    import pytz  # noqa
    from dateutil import rrule  # noqa

    if start_date:
        start_date = (
            datetime.strptime(start_date, "%Y-%m-%d")
            if isinstance(start_date, str)
            else start_date
        )
    if end_date:
        end_date = (
            datetime.strptime(end_date, "%Y-%m-%d")
            if isinstance(end_date, str)
            else end_date
        )
    user_agent = get_random_agent()
    results: list[dict] = []
    symbol = symbol.upper().replace("-", ".").replace(".TO", "").replace(".TSX", "")
    start_date = (
        (datetime.now() - timedelta(weeks=4)).date()
        if start_date is None
        else start_date
    )
    end_date = datetime.now().date() if end_date is None else end_date
    # This is the first date of available intraday data.
    date_check = datetime(2022, 4, 12).date()
    start_date = max(start_date, date_check)
    if end_date < date_check:  # type: ignore
        end_date = datetime.now().date()
    # Generate a list of dates from start_date to end_date with a frequency of 3 weeks
    dates = list(rrule.rrule(rrule.WEEKLY, interval=4, dtstart=start_date, until=end_date))  # type: ignore

    if dates[-1] != end_date:
        dates.append(end_date)  # type: ignore

    # Create a list of 4-week chunks
    chunks = [
        (dates[i], dates[i + 1] - timedelta(days=1)) for i in range(len(dates) - 1)
    ]

    # Adjust the end date of the last chunk to be the final end date
    chunks[-1] = (chunks[-1][0], end_date)  # type: ignore

    async def create_task(start, end, results):
        """Create a task from a start and end date chunk."""
        # Create a datetime object representing 9:30 AM on the date
        start_obj = datetime.combine(start, time(9, 30))
        end_obj = datetime.combine(end, time(16, 0))

        # Convert the datetime object to EST
        est = pytz.timezone("US/Eastern")
        start_obj_est = est.localize(start_obj)
        end_obj_est = est.localize(end_obj)

        # Convert the datetime object to a timestamp
        start_time = int(start_obj_est.timestamp())
        end_time = int(end_obj_est.timestamp())

        payload = gql.get_timeseries_payload.copy()
        payload["variables"]["interval"] = None
        if payload["variables"].get("start"):
            payload["variables"].pop("start")
        payload["variables"]["startDateTime"] = int(start_time)
        if payload["variables"].get("end"):
            payload["variables"].pop("end")
        payload["variables"]["endDateTime"] = int(end_time)
        payload["variables"]["interval"] = interval
        payload["variables"]["symbol"] = symbol
        if payload["variables"].get("freq"):
            payload["variables"].pop("freq")
        url = "https://app-money.tmx.com/graphql"
        data = await get_data_from_gql(
            method="POST",
            url=url,
            data=json.dumps(payload),
            headers={
                "authority": "app-money.tmx.com",
                "referer": f"https://money.tmx.com/en/quote/{symbol}",
                "locale": "en",
                "Content-Type": "application/json",
                "User-Agent": user_agent,
                "Accept": "*/*",
            },
            timeout=3,
        )

        async def try_again():
            """Try again if the request fails."""
            return await get_data_from_gql(
                method="POST",
                url=url,
                data=json.dumps(payload),
                headers={
                    "authority": "app-money.tmx.com",
                    "referer": f"https://money.tmx.com/en/quote/{symbol}",
                    "locale": "en",
                    "Content-Type": "application/json",
                    "User-Agent": user_agent,
                    "Accept": "*/*",
                },
                timeout=3,
            )

        if isinstance(data, str):
            data = await try_again()

        if data.get("data") and data["data"].get("getTimeSeriesData"):
            result = data["data"].get("getTimeSeriesData")
            results.extend(result)

        return results

    tasks = [create_task(chunk[0], chunk[1], results) for chunk in chunks]

    await asyncio.gather(*tasks)

    if len(results) > 0 and "dateTime" in results[0]:
        results = sorted(results, key=lambda x: x["dateTime"], reverse=False)

    return results