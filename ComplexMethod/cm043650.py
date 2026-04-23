async def fetch_callback(response, session):
            """Use callback for pagination."""
            data = await response.json()
            error = data.get("error", None)
            if error:
                message = data.get("message", "")
                if "api key" in message.lower():
                    raise UnauthorizedError(
                        f"Unauthorized Intrinio request -> {message}"
                    )
                raise OpenBBError(f"Error: {error} -> {message}")

            if data.get("estimates") and len(data.get("estimates")) > 0:  # type: ignore
                results.extend(data.get("estimates"))  # type: ignore
                while data.get("next_page"):  # type: ignore
                    next_page = data["next_page"]  # type: ignore
                    next_url = f"{url}&next_page={next_page}"
                    data = await amake_request(next_url, session=session, **kwargs)
                    if "estimates" in data and len(data.get("estimates")) > 0:  # type: ignore
                        results.extend(data.get("estimates"))  # type: ignore
            return results