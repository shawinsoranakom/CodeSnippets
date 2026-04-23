async def get_daily_price_history(
    symbol: str,
    start_date: str | dateType | None = None,
    end_date: str | dateType | None = None,
    adjustment: Literal[
        "splits_only", "unadjusted", "splits_and_dividends"
    ] = "splits_only",
):
    """Get historical price data."""
    # pylint: disable=import-outside-toplevel
    import json  # noqa
    import asyncio  # noqa
    from dateutil import rrule  # noqa

    start_date = (
        datetime.strptime(start_date, "%Y-%m-%d")
        if isinstance(start_date, str)
        else start_date
    )
    end_date = (
        datetime.strptime(end_date, "%Y-%m-%d")
        if isinstance(end_date, str)
        else end_date
    )
    user_agent = get_random_agent()
    results: list[dict] = []
    symbol = symbol.upper().replace("-", ".").replace(".TO", "").replace(".TSX", "")
    start_date = (
        (datetime.now() - timedelta(weeks=52)).date()
        if start_date is None
        else start_date
    )
    end_date = datetime.now() if end_date is None else end_date

    # Generate a list of dates from start_date to end_date with a frequency of 4 weeks
    dates = list(
        rrule.rrule(rrule.WEEKLY, interval=4, dtstart=start_date, until=end_date)
    )

    # Add end_date to the list if it's not there already
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
        payload = gql.get_company_price_history_payload.copy()
        payload["variables"]["adjusted"] = adjustment != "unadjusted"  # noqa: SIM211
        payload["variables"]["adjustmentType"] = (
            "SO" if adjustment == "splits_only" else None
        )
        payload["variables"]["end"] = end.strftime("%Y-%m-%d")
        payload["variables"]["start"] = start.strftime("%Y-%m-%d")
        payload["variables"]["symbol"] = symbol
        payload["variables"]["unadjusted"] = adjustment == "unadjusted"  # noqa: SIM210
        if payload["variables"]["adjustmentType"] is None:
            payload["variables"].pop("adjustmentType")
        url = "https://app-money.tmx.com/graphql"

        async def try_again():
            """Try again if it fails."""
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

        try:
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
        except Exception:
            data = await try_again()

        if isinstance(data, str):
            data = await try_again()

        if data.get("data") and data["data"].get("getCompanyPriceHistory"):
            results.extend(data["data"].get("getCompanyPriceHistory"))

        return results

    tasks = [create_task(chunk[0], chunk[1], results) for chunk in chunks]

    await asyncio.gather(*tasks)

    results = [d for d in results if d["openPrice"] is not None]

    return sorted(results, key=lambda x: x["datetime"], reverse=False)