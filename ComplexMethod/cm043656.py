async def response_callback(response: ClientResponse, session: ClientSession):
            """Async response callback."""
            results = await response.json()
            if "trades" in results and len(results.get("trades")) > 0:  # type: ignore
                data.extend(
                    sorted(
                        results["trades"],  # type: ignore
                        key=lambda x: x["timestamp"],
                        reverse=True,
                    )
                )
                records = len(data)
                while (
                    "next_page" in results
                    and results.get("next_page") is not None  # type: ignore
                    and records < query.limit
                ):
                    next_page = results["next_page"]  # type: ignore
                    next_url = f"{url}&next_page={next_page}"
                    results = await amake_request(next_url, session=session, **kwargs)
                    if "trades" in results and len(results.get("trades")) > 0:  # type: ignore
                        data.extend(
                            sorted(
                                results["trades"],  # type: ignore
                                key=lambda x: x["timestamp"],
                                reverse=True,
                            )
                        )
                        records = len(data)
            return data