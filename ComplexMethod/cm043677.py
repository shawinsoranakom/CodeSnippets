async def callback(response: ClientResponse, session: ClientSession) -> list:
            """Return the response."""
            init_response: Any = await response.json()
            all_data: list = []
            init_data = init_response.get("historical_data", [])

            if init_data and isinstance(init_data, list):
                all_data.extend(init_data)

            if query.all_pages:
                next_page = init_response.get("next_page", None)
                while next_page:
                    if query.limit and query.limit > 100:
                        await asyncio.sleep(query.sleep or 1.0)

                    url = response.url.update_query(next_page=next_page).human_repr()
                    response_data = await session.get_json(url)

                    all_data.extend(response_data.get("historical_data", []))  # type: ignore
                    next_page = response_data.get("next_page", None)  # type: ignore

            return all_data