async def response_callback(
    response: ClientResponse, _: ClientSession
) -> dict | list[dict]:
    """Use callback for async_request."""
    data = await response.json()

    if isinstance(data, dict) and "error" in data:
        message = data.get("message", "")
        error = data.get("error", "")
        if "api key" in message.lower() or error.startswith(
            "You do not have sufficient access to view this data"
        ):
            raise UnauthorizedError(
                f"Unauthorized Intrinio request -> {message} -> {error}"
            )

        raise OpenBBError(f"Error in Intrinio request -> {message} -> {error}")

    if isinstance(data, (str, float)):
        data = {"value": data}

    if isinstance(data, list) and len(data) == 0:
        raise EmptyDataError()

    return data