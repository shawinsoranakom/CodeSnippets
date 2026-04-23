async def get_partial_function_dependency(
    value: Annotated[
        str, Depends(partial(function_dependency, "partial-function-dependency"))
    ],
) -> str:
    return value