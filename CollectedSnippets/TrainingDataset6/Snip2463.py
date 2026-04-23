async def get_partial_synchronous_method_dependency(
    value: Annotated[
        str,
        Depends(
            partial(
                methods_dependency.synchronous, "partial-synchronous-method-dependency"
            )
        ),
    ],
) -> str:
    return value