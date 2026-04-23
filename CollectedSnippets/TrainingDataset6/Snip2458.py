async def get_partial_async_gen_dependency(
    value: Annotated[
        str, Depends(partial(async_gen_dependency, "partial-async-gen-dependency"))
    ],
) -> str:
    return value