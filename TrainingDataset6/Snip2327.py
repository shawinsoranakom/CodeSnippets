async def get_async_callable_gen_dependency_class(
    value: str, instance: AsyncCallableGenDependency = Depends()
):
    return await instance(value).__anext__()