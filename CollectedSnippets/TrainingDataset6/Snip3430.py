async def read_required_list_str(p: Annotated[list[str], Form()]):
    return {"p": p}