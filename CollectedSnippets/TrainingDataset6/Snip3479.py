async def read_model_optional_str(p: Annotated[FormModelOptionalStr, Form()]):
    return {"p": p.p}