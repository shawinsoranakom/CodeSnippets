async def get_wrapped_class_instance_gen_dependency(
    value: bool = Depends(wrapped_class_instance_gen_dep),
):
    return value