async def get_historical_ohlc(query, credentials, **kwargs: Any) -> list[dict]:
    """Return the raw data from the FMP endpoint."""
    # pylint: disable=import-outside-toplevel
    import asyncio  # noqa
    from openbb_core.provider.utils.helpers import (
        amake_request,
    )
    from warnings import warn

    api_key = credentials.get("fmp_api_key") if credentials else ""

    base_url = "https://financialmodelingprep.com/stable/"

    if hasattr(query, "adjustment") and query.adjustment == "unadjusted":
        base_url += "historical-price-eod/non-split-adjusted?"
    elif hasattr(query, "adjustment") and query.adjustment == "splits_and_dividends":
        base_url += "historical-price-eod/dividend-adjusted?"
    elif query.interval == "1d":
        base_url += "historical-price-eod/full?"
    elif query.interval == "1m":
        base_url += "historical-chart/1min?"
    elif query.interval == "5m":
        base_url += "historical-chart/5min?"
    elif query.interval in ["60m", "1h"]:
        query.interval = "60m"
        base_url += "historical-chart/1hour?"

    query_str = get_querystring(
        query.model_dump(), ["symbol", "adjustment", "interval"]
    )
    symbols = query.symbol.split(",")

    results: list = []
    messages: list = []

    async def get_one(symbol):
        """Get data for one symbol."""
        url = f"{base_url}symbol={symbol}&{query_str}&apikey={api_key}"
        data: list = []
        response = await amake_request(
            url, response_callback=response_callback, **kwargs
        )

        if isinstance(response, dict) and response.get("Error Message"):
            message = (
                f"Error fetching data for {symbol}: {response.get('Error Message', '')}"
            )
            warn(message)
            messages.append(message)

        if isinstance(response, list) and len(response) > 0:
            data = response

        elif isinstance(response, dict) and response.get("historical"):
            data = response.get("historical", [])

        if not data:
            message = f"No data found for {symbol}."
            warn(message)
            messages.append(message)

        elif data:
            for d in data:
                d["symbol"] = symbol
                results.append(d)

    await asyncio.gather(*[get_one(symbol) for symbol in symbols])

    if not results:
        raise EmptyDataError(
            f"{str(','.join(messages)).replace(',', ' ') if messages else 'No data found'}"
        )

    return results