async def get_partial_synchronous_method_gen_dependency(
    value: Annotated[
        str,
        Depends(
            partial(
                methods_dependency.synchronous_gen,
                "partial-synchronous-method-gen-dependency",
            )
        ),
    ],
) -> str:
    return value