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

            estimates = data.get("ebitda_consensus", [])  # type: ignore
            if estimates and len(estimates) > 0:
                results.extend(estimates)
                while data.get("next_page"):  # type: ignore
                    next_page = data["next_page"]  # type: ignore
                    next_url = f"{url}&next_page={next_page}"
                    data = await amake_request(next_url, session=session, **kwargs)
                    consensus = (
                        data.get("ebitda_consensus")
                        if isinstance(data, dict) and "ebitda_consensus" in data
                        else []
                    )
                    if consensus:
                        results.extend(consensus)  # type: ignore
            return results