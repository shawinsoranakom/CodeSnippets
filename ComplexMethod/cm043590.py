async def get_defined_screener(
    name: str | None = None,
    body: dict[str, Any] | None = None,
    limit: int | None = None,
):
    """Get a predefined screener."""
    # pylint: disable=import-outside-toplevel
    import yfinance as yf  # noqa
    from openbb_core.provider.utils.helpers import (
        safe_fromtimestamp,
    )
    from pytz import timezone

    if name and name not in PREDEFINED_SCREENERS:
        raise ValueError(
            f"Invalid predefined screener name: {name}\n    Valid names: {PREDEFINED_SCREENERS}"
        )

    results: list = []

    offset = 0

    response = yf.screen(
        name,  # type: ignore
        size=250,
        offset=offset,
    )

    if not response.get("quotes"):
        raise EmptyDataError("No data found for the predefined screener.")

    total_results = response["total"]
    results.extend(response["quotes"])

    while len(results) < total_results:
        if limit is not None and len(results) >= limit:
            break
        offset = len(results)
        res = yf.screen(
            name,  # type: ignore
            size=250,
            offset=offset,
        )
        if not res:
            break
        results.extend(res.get("quotes", []))

    output: list = []
    symbols: set = set()

    for item in results:
        sym = item.get("symbol")

        if not sym or sym in symbols:
            continue

        symbols.add(sym)
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

        if not output:
            raise EmptyDataError("No data found for the predefined screener.")

    return output[:limit] if limit is not None else output