async def async_model_with_response_model(
    dep: Annotated[int, Depends(dep_b)],
):
    return ItemOut(name="foo", value=123, dep=dep)