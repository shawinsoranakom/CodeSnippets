async def get_wrapped_class_instance_dependency(
    value: bool = Depends(wrapped_class_instance_dep),
):
    return value