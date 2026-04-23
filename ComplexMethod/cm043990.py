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