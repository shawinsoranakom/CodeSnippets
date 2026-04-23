async def get_wrapped_class_instance_async_dependency(
    value: bool = Depends(wrapped_class_instance_async_dep),
):
    return value