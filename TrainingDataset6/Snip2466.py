async def get_partial_asynchronous_method_gen_dependency(
    value: Annotated[
        str,
        Depends(
            partial(
                methods_dependency.asynchronous_gen,
                "partial-asynchronous-method-gen-dependency",
            )
        ),
    ],
) -> str:
    return value