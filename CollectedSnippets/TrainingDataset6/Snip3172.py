async def read_required_list_str(p: Annotated[list[str], Body(embed=True)]):
    return {"p": p}