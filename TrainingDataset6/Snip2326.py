async def get_async_callable_dependency_class(
    value: str, instance: AsyncCallableDependency = Depends()
):
    return await instance(value)