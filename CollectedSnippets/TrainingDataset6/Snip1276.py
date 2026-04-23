async def create_item(item: Annotated[Item, Body(embed=True)]) -> Item:
    return item