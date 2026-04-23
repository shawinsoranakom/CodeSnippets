async def get_wrapped_class_instance_dependency_async_wrapper(
    value: bool = Depends(wrapped_class_instance_dep_async_wrapper),
):
    return value