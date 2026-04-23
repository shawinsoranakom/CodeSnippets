async def callback(
            response: ClientResponse, session: ClientSession
        ) -> list[dict]:
            """Return the response."""
            init_response = await response.json()

            if message := init_response.get(  # type: ignore
                "error"
            ) or init_response.get(  # type: ignore
                "message"
            ):
                warnings.warn(message=str(message), category=OpenBBWarning)
                return []

            symbol = response.url.parts[-2]  # type: ignore
            tag = response.url.parts[-1]  # type: ignore

            all_data: list = init_response.get("historical_data", [])  # type: ignore
            all_data = [{**item, "symbol": symbol, "tag": tag} for item in all_data]

            next_page = init_response.get("next_page", None)  # type: ignore
            while next_page:
                url = response.url.update_query(next_page=next_page).human_repr()  # type: ignore
                response_data = await session.get_json(url)

                if message := response_data.get("error") or response_data.get("message"):  # type: ignore
                    warnings.warn(message=message, category=OpenBBWarning)
                    return []

                symbol = response.url.parts[-2]  # type: ignore
                tag = response_data.url.parts[-1]  # type: ignore

                response_data = response_data.get("historical_data", [])  # type: ignore
                response_data = [
                    {**item, "symbol": symbol, "tag": tag} for item in response_data
                ]

                all_data.extend(response_data)
                next_page = response_data.get("next_page", None)  # type: ignore

            return all_data