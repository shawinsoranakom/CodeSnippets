async def get_async_wrapped_dependency(value: bool = Depends(async_wrapped_dependency)):
    return value