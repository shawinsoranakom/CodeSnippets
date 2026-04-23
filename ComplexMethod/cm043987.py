async def response_callback(response, _):
    """Use callback for make_request."""
    if response.status != 200:
        msg = await response.text()
        code = response.status
        raise UnauthorizedError(f"Unauthorized FMP request -> {code} -> {msg}")

    data = await response.json()

    if isinstance(data, dict):
        error_message = data.get("Error Message", data.get("error"))

        if error_message is not None:
            conditions = (
                "upgrade" in error_message.lower()
                or "exclusive endpoint" in error_message.lower()
                or "special endpoint" in error_message.lower()
                or "premium query parameter" in error_message.lower()
                or "subscription" in error_message.lower()
                or "unauthorized" in error_message.lower()
                or "premium" in error_message.lower()
            )

            if conditions:
                raise UnauthorizedError(f"Unauthorized FMP request -> {error_message}")

            raise OpenBBError(
                f"FMP Error Message -> Status code: {response.status} -> {error_message}"
            )

    return data