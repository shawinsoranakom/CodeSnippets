async def read_model_optional_str(p: Annotated[HeaderModelOptionalStr, Header()]):
    return {"p": p.p}