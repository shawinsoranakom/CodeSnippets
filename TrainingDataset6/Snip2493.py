async def get_wrapped_dependency(value: bool = Depends(wrapped_dependency)):
    return value