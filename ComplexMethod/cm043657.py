async def callback(response, session):
            """Response callback."""
            result = await response.json()

            if isinstance(result, dict) and "error" in result:
                if "api key" in result.get("message", "").lower():
                    raise UnauthorizedError(
                        f"Unauthorized Intrinio request -> {result.get('message')}"
                    )
                raise OpenBBError(f"Error in Intrinio request -> {result}")

            symbol = response.url.parts[-2]
            _data = result.get("news", [])
            data = []
            data.extend([{"symbol": symbol, **d} for d in _data])
            articles = len(data)
            next_page = result.get("next_page")
            # query.limit can be None...
            limit = query.limit or 2500
            while next_page and limit > articles:
                url = (
                    f"{base_url}/{symbol}/news?{query_str}"
                    + f"&page_size={query.limit}&api_key={api_key}&next_page={next_page}"
                )
                result = await get_data(url, session=session, **kwargs)
                _data = result.get("news", [])
                if _data:
                    data.extend([{"symbol": symbol, **d} for d in _data])
                    articles = len(data)
                next_page = result.get("next_page")
            return data