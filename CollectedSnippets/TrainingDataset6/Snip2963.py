async def hidden_cookie(
    hidden_cookie: str | None = Cookie(default=None, include_in_schema=False),
):
    return {"hidden_cookie": hidden_cookie}