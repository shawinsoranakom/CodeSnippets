async def get_partial_async_function_dependency(
    value: Annotated[
        str,
        Depends(
            partial(async_function_dependency, "partial-async-function-dependency")
        ),
    ],
) -> str:
    return value