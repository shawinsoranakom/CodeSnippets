async def get_partial_asynchronous_method_dependency(
    value: Annotated[
        str,
        Depends(
            partial(
                methods_dependency.asynchronous,
                "partial-asynchronous-method-dependency",
            )
        ),
    ],
) -> str:
    return value