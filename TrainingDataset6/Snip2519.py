async def get_async_wrapped_gen_dependency_async_wrapper(
    value: bool = Depends(async_wrapped_gen_dependency_async_wrapper),
):
    return value