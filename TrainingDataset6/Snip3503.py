async def read_model_required_str(p: Annotated[FormModelRequiredStr, Form()]):
    return {"p": p.p}