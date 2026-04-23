async def read_model_optional_str(p: Annotated[QueryModelOptionalStr, Query()]):
    return {"p": p.p}