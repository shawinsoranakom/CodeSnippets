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
                if "," in query.symbol:
                    for d in data:
                        d["symbol"] = symbol
                results.extend(data)