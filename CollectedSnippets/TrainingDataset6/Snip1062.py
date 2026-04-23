async def create_author_items(author_id: str, items: list[Item]):  # (5)
    return {"name": author_id, "items": items}