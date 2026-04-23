async def get_wrapped_dependency_async_wrapper(
    value: bool = Depends(wrapped_dependency_async_wrapper),
):
    return value