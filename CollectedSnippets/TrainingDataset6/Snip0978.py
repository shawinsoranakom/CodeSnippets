async def update_item(item_id: int, item: Item):
    return {"item_id": item_id, **item.model_dump()}