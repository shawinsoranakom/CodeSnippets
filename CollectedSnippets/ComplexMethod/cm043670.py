async def callback(response, session):
            """Response callback."""
            result = await response.json()

            if isinstance(result, dict) and "error" in result:
                if "api key" in result.get("message", "").lower():
                    raise UnauthorizedError(
                        f"Unauthorized Intrinio request -> {result.get('message')}"
                    )
                raise OpenBBError(f"Error in Intrinio request -> {result}")

            _data = result.get("news", [])
            data = []
            data.extend([x for x in _data if not (x["url"] in seen or seen.add(x["url"]))])  # type: ignore
            articles = len(data)
            next_page = result.get("next_page")
            while next_page and articles < query.limit:
                url = f"{base_url}/news?{query_str}&page_size={query.limit}&api_key={api_key}&next_page={next_page}"
                result = await get_data(url, session=session, **kwargs)
                _data = result.get("news", [])
                if _data:
                    # Remove duplicates based on URL
                    data.extend([x for x in _data if not (x["url"] in seen or seen.add(x["url"]))])  # type: ignore
                    articles = len(data)
                next_page = result.get("next_page")
            return sorted(data, key=lambda x: x["publication_date"], reverse=True)[
                : query.limit
            ]