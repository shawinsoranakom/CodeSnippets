async def async_validated(
    item: ItemIn,
    dep: Annotated[int, Depends(dep_b)],
):
    return ItemOut(name=item.name, value=item.value, dep=dep)