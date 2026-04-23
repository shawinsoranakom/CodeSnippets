async def get_class_instance_async_wrapped_async_dependency(
    value: bool = Depends(class_instance_async_wrapped_async_dep),
):
    return value