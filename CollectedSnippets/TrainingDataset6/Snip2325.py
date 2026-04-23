async def get_callable_gen_dependency_class(
    value: str, instance: CallableGenDependency = Depends()
):
    return next(instance(value))