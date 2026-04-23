def zip_schema(
    schema: _C.FunctionSchema, args: tuple[Any, ...], kwargs: dict[str, Any]
) -> Iterable[tuple[_C.Argument, Any]]:
    """zips schema.arguments and (args, kwargs) together.

    Assumes that (args, kwargs) were the inputs to some torch._ops.OpOverload:
    that is, (args, kwargs) must be bindable to the schema (args, kwargs).
    """
    if len(schema.arguments) < len(args) + len(kwargs):
        raise AssertionError(
            f"schema has {len(schema.arguments)} arguments but got {len(args)} args and {len(kwargs)} kwargs"
        )
    for i in range(len(schema.arguments)):
        info = schema.arguments[i]
        if info.kwarg_only:
            if info.name in kwargs:
                yield info, kwargs[info.name]
            continue
        if i >= len(args):
            if not info.kwarg_only and info.name in kwargs:
                yield info, kwargs[info.name]
            # args that are equal to their default values are not populated
            # if they are followed by args that are equal to their defaults.
            # Skip these.
            continue
        yield info, args[i]
    return