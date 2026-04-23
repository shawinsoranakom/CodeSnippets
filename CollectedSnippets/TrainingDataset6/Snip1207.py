async def read_items(headers: Annotated[CommonHeaders, Header()]):
    return headers