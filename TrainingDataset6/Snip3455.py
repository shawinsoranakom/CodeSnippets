async def read_model_optional_list_str(p: Annotated[FormModelOptionalListStr, Form()]):
    return {"p": p.p}