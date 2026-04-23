async def get_partial_gen_dependency(
    value: Annotated[str, Depends(partial(gen_dependency, "partial-gen-dependency"))],
) -> str:
    return value