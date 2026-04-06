async def get_class_instance_wrapped_gen_dependency(
    value: bool = Depends(class_instance_wrapped_gen_dep),
):
    return value