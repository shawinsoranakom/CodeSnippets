async def read_required_list_alias(
    p: Annotated[list[str], Body(embed=True, alias="p_alias")],
):
    return {"p": p}