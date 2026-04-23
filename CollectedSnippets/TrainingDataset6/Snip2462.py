async def get_partial_async_callable_gen_dependency(
    value: Annotated[
        str,
        Depends(
            partial(
                async_callable_gen_dependency, "partial-async-callable-gen-dependency"
            )
        ),
    ],
) -> str:
    return value