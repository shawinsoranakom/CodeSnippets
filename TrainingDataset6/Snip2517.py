async def get_wrapped_gen_dependency_async_wrapper(
    value: bool = Depends(wrapped_gen_dependency_async_wrapper),
):
    return value