async def get_partial_callable_dependency(
    value: Annotated[
        str, Depends(partial(callable_dependency, "partial-callable-dependency"))
    ],
) -> str:
    return value