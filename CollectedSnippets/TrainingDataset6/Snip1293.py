async def read_items(filter_query: FilterParams = Query()):
    return filter_query