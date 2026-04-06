async def get_callable_dependency_class(
    value: str, instance: CallableDependency = Depends()
):
    return instance(value)