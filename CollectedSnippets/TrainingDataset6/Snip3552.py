async def read_model_optional_list_str(
    p: Annotated[HeaderModelOptionalListStr, Header()],
):
    return {"p": p.p}