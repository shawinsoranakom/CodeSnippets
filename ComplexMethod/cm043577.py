async def get_one(symbol):
            """Get the data for one ticker symbol."""
            result: dict = {}
            ticker: dict = {}
            try:
                _ticker = await asyncio.to_thread(lambda: Ticker(symbol))
                ticker = await asyncio.to_thread(lambda: _ticker.get_info())
                major_holders = await asyncio.to_thread(
                    lambda: _ticker.get_major_holders(as_dict=True).get("Value")
                )
                if major_holders:
                    ticker.update(major_holders)  # type: ignore
            except Exception as e:
                messages.append(
                    f"Error getting data for {symbol} -> {e.__class__.__name__}: {e}"
                )
            if ticker:
                for field in fields:
                    if field in ticker:
                        result[field] = ticker.get(field, None)
                if result and result.get("sharesOutstanding") is not None:
                    results.append(result)