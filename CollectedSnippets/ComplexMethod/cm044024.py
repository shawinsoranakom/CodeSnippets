async def aextract_data(
        query: TradierEquityHistoricalQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the Tradier endpoint."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        from openbb_core.provider.utils.helpers import (
            amake_request,
            safe_fromtimestamp,
        )  # noqa
        from pytz import timezone  # noqa

        api_key = credentials.get("tradier_api_key") if credentials else ""
        sandbox = True

        if api_key and credentials.get("tradier_account_type") not in ["sandbox", "live"]:  # type: ignore
            raise OpenBBError(
                "Invalid account type for Tradier. Must be either 'sandbox' or 'live'."
            )

        if api_key:
            sandbox = (
                credentials.get("tradier_account_type") == "sandbox"
                if credentials
                else False
            )

        BASE_URL = (
            "https://api.tradier.com/"
            if sandbox is False
            else "https://sandbox.tradier.com/"
        )
        HEADERS = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }

        session_filter = "all" if query.extended_hours is True else "open"
        interval = INTERVALS_DICT[query.interval]
        end_point = "timesales" if query.interval in ["1m", "5m", "15m"] else "history"
        results = []
        start_time = "09:30" if query.extended_hours is False else "00:00"
        end_time = "16:00" if query.extended_hours is False else "20:00"

        async def get_one(symbol):
            """Get data for one symbol."""
            result = []

            url = (
                f"{BASE_URL}v1/markets/{end_point}?symbol={symbol}&interval={interval}"
            )

            if query.interval in ["1m", "5m", "15m"]:
                url += (
                    f"&start={query.start_date}%20{start_time}"  # type: ignore
                    f"&end={query.end_date}%20{end_time}&session_filter={session_filter}"  # type: ignore
                )
            if query.interval in ["1d", "1W", "1M"]:
                url += f"&start={query.start_date}&end={query.end_date}"

            data = await amake_request(url, headers=HEADERS)

            if interval in ["daily", "weekly", "monthly"] and data.get("history"):  # type: ignore
                result = data["history"].get("day")  # type: ignore
                if len(query.symbol.split(",")) > 1:
                    for r in result:
                        r["symbol"] = symbol

            if interval in ["1min", "5min", "15min"] and data.get("series"):  # type: ignore
                result = data["series"].get("data")  # type: ignore
                for r in result:
                    if len(query.symbol.split(",")) > 1:
                        r["symbol"] = symbol
                    _ = r.pop("time")
                    r["timestamp"] = (
                        safe_fromtimestamp(r.get("timestamp"))
                        .replace(microsecond=0)
                        .astimezone(timezone("America/New_York"))
                    )

            if result != []:
                results.extend(result)
            if result == []:
                warn(f"No data found for {symbol}.")

        symbols = query.symbol.split(",")
        tasks = [get_one(symbol) for symbol in symbols]
        await asyncio.gather(*tasks)

        if len(results) == 0:
            raise EmptyDataError("No results found.")

        return results