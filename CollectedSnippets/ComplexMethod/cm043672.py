async def get_one(symbol):
            """Get data for one symbol."""
            url_params = (
                f"{symbol}/marketcap?{frequency}start_date={start_date}"
                f"&end_date={end_date}&page_size=10000"
                f"&api_key={api_key}"
            )
            url = f"{base_url}{url_params}"
            try:
                response = await amake_request(url, response_callback=response_callback)
            except OpenBBError as e:
                if "Cannot look up this item/identifier combination" in str(e):
                    msg = f"Symbol not found: {symbol}"
                    messages.append(msg)
                    return
                raise e from e

            if not isinstance(response, dict):
                raise OpenBBError(
                    f"Unexpected response format, expected a dictionary, got {response.__class__.__name__}"
                )

            if not response:
                msg = f"No data found for symbol: {symbol}"
                messages.append(msg)

            if response.get("historical_data"):
                data = response.get("historical_data", {})
                result = [
                    {"symbol": symbol, **item} for item in data if item.get("value")
                ]
                results.extend(result)

            return