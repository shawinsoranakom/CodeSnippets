async def get_class_instance_async_wrapped_dependency(
    value: bool = Depends(class_instance_async_wrapped_dep),
):
    return value