async def get_weekly_or_monthly_price_history(
    symbol: str,
    start_date: str | dateType | None = None,
    end_date: str | dateType | None = None,
    interval: Literal["month", "week"] = "month",
):
    """Get historical price data."""
    # pylint: disable=import-outside-toplevel
    import json

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
        (datetime.now() - timedelta(weeks=52 * 100)).date()
        if start_date is None
        else start_date
    )
    end_date = datetime.now() if end_date is None else end_date

    payload = gql.get_timeseries_payload.copy()
    if "interval" in payload["variables"]:
        payload["variables"].pop("interval")
    if "startDateTime" in payload["variables"]:
        payload["variables"].pop("startDateTime")
    if "endDateTime" in payload["variables"]:
        payload["variables"].pop("endDateTime")
    payload["variables"]["symbol"] = symbol
    payload["variables"]["freq"] = interval
    payload["variables"]["end"] = (
        end_date.strftime("%Y-%m-%d") if isinstance(end_date, dateType) else end_date
    )
    payload["variables"]["start"] = (
        start_date.strftime("%Y-%m-%d")
        if isinstance(start_date, dateType)
        else start_date
    )
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
        results = data["data"].get("getTimeSeriesData")
        results = sorted(results, key=lambda x: x["dateTime"], reverse=False)
    return results