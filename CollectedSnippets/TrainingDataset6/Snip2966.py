async def hidden_query(
    hidden_query: str | None = Query(default=None, include_in_schema=False),
):
    return {"hidden_query": hidden_query}