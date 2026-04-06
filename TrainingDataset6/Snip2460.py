async def get_partial_callable_gen_dependency(
    value: Annotated[
        str,
        Depends(partial(callable_gen_dependency, "partial-callable-gen-dependency")),
    ],
) -> str:
    return value