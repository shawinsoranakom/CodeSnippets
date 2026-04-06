async def async_dict_with_response_model(
    dep: Annotated[int, Depends(dep_b)],
):
    return {"name": "foo", "value": 123, "dep": dep}