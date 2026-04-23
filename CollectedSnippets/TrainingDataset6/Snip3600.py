async def read_model_required_str(p: Annotated[HeaderModelRequiredStr, Header()]):
    return {"p": p.p}