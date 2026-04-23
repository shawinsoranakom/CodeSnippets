async def get_wrapped_gen_dependency(value: bool = Depends(wrapped_gen_dependency)):
    return value