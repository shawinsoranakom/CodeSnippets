async def dep3(
    dep1: Annotated[list[str], Security(security1, scopes=["scope1"])],
    dep2: Annotated[list[str], Security(security2, scopes=["scope2"])],
):
    return {"dep1": dep1, "dep2": dep2}