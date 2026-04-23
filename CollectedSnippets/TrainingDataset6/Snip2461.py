async def get_partial_async_callable_dependency(
    value: Annotated[
        str,
        Depends(
            partial(async_callable_dependency, "partial-async-callable-dependency")
        ),
    ],
) -> str:
    return value