async def get_wrapped_class_dependency_async_wrapper(
    value: ClassDep = Depends(wrapped_class_dep_async_wrapper),
):
    return value.value