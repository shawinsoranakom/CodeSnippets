async def read_model_required_str(p: Annotated[CookieModelRequiredStr, Cookie()]):
    return {"p": p.p}