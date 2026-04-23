async def get_custom_screener(
    body: dict[str, Any],
    limit: int | None = None,
    region: str = "US",
):
    """Get a custom screener."""
    # pylint: disable=import-outside-toplevel
    from openbb_core.provider.utils.helpers import (  # noqa
        safe_fromtimestamp,
    )
    from pytz import timezone
    from yfinance.data import YfData

    params_dict = {
        "corsDomain": "finance.yahoo.com",
        "formatted": "false",
        "lang": "en-US",
        "region": region,
    }
    _data = YfData()
    results: list = []
    body = body.copy()
    response = _data.post(
        "https://query2.finance.yahoo.com/v1/finance/screener",
        body=body,
        params=params_dict,
    )
    response.raise_for_status()
    res = response.json()["finance"]["result"][0]

    if not res.get("quotes"):
        raise EmptyDataError("No data found for the predefined screener.")

    results.extend(res["quotes"])
    total_results = res["total"]

    while len(results) < total_results:
        if limit is not None and len(results) >= limit:
            break
        offset = len(results)
        body["offset"] = offset
        response = _data.post(
            "https://query2.finance.yahoo.com/v1/finance/screener",
            body=body,
            params=params_dict,
        )
        if not res:
            break
        res = response.json()["finance"]["result"][0]
        results.extend(res.get("quotes", []))

    output: list = []

    for item in results:
        tz = item["exchangeTimezoneName"]
        earnings_date = (
            safe_fromtimestamp(item["earningsTimestamp"], timezone(tz)).strftime("%Y-%m-%d %H:%M:%S%z")  # type: ignore
            if item.get("earningsTimestamp")
            else None
        )
        item["earnings_date"] = earnings_date
        result = {k: item.get(k, None) for k in SCREENER_FIELDS}
        if result.get("regularMarketChange") and result.get("regularMarketVolume"):
            output.append(result)

    return output[:limit] if limit is not None else output