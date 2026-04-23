async def get_one(symbol):
            """Get the data for one ticker symbol."""
            result: dict = {}
            ticker: dict = {}
            try:
                ticker = await asyncio.to_thread(lambda: Ticker(symbol).get_info())
            except Exception as e:
                messages.append(
                    f"Error getting data for {symbol} -> {e.__class__.__name__}: {e}"
                )
            if ticker:
                quote_type = ticker.pop("quoteType", "")
                if quote_type == "ETF":
                    try:
                        for field in fields:
                            if field in ticker and ticker.get(field) is not None:
                                result[field] = ticker.get(field, None)
                        if "firstTradeDateEpochUtc" in result:
                            _first_trade = result.pop("firstTradeDateEpochUtc")
                            if (
                                "fundInceptionDate" not in result
                                and _first_trade is not None
                            ):
                                result["fundInceptionDate"] = safe_fromtimestamp(
                                    _first_trade
                                )
                    except Exception as e:
                        messages.append(
                            f"Error processing data for {symbol} -> {e.__class__.__name__}: {e}"
                        )
                        result = {}
                if quote_type != "ETF":
                    messages.append(f"{symbol} is not an ETF.")
                if result:
                    results.append(result)