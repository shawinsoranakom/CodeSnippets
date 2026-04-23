async def get_wrapped_class_dependency(value: ClassDep = Depends(wrapped_class_dep)):
    return value.value