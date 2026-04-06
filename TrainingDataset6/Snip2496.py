async def get_async_wrapped_gen_dependency(
    value: bool = Depends(async_wrapped_gen_dependency),
):
    return value