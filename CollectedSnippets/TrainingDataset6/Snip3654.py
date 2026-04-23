async def read_model_optional_list_str(
    p: Annotated[QueryModelOptionalListStr, Query()],
):
    return {"p": p.p}