async def sse_items_dict():
    for item in items:
        yield {"name": item.name, "description": item.description}