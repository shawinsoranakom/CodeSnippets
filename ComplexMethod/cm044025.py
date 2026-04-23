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