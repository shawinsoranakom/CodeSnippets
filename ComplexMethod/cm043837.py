async def get_one(symbol):
            """Get data for one symbol."""
            url = f"{base_url}/{symbol}/prices?{query_str}&resampleFreq={frequency}&token={api_key}"
            data = None
            try:
                data = await get_data(url)
            except UnauthorizedError as e:
                raise e from e
            except OpenBBError as e:
                if (
                    e.original
                    and isinstance(e.original, str)
                    and "ticker" in e.original.lower()
                ):
                    messages.append(e.original)
                else:
                    messages.append(f"{symbol}: {e.original}")

            if isinstance(data, list):
                for d in data:
                    ticker = d.pop("ticker", None)
                    if ticker and len(symbols) > 1:
                        d["ticker"] = d["ticker"].upper()

                    if query.interval.endswith("d"):
                        d["date"] = to_datetime(d["date"]).date()
                    else:
                        d["date"] = to_datetime(d["date"], utc=True)

                results.extend(data)