async def hidden_header(
    hidden_header: str | None = Header(default=None, include_in_schema=False),
):
    return {"hidden_header": hidden_header}