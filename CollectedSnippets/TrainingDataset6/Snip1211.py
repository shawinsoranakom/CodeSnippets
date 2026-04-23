async def read_items(
    headers: Annotated[CommonHeaders, Header(convert_underscores=False)],
):
    return headers