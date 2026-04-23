async def read_items(filter_query: Annotated[FilterParams, Query()]):
    return filter_query