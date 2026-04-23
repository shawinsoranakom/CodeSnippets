async def read_model_optional_str(p: Annotated[CookieModelOptionalStr, Cookie()]):
    return {"p": p.p}