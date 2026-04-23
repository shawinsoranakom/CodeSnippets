async def read_model_required_str(p: Annotated[QueryModelRequiredStr, Query()]):
    return {"p": p.p}