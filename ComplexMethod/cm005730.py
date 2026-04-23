def _convert_type_hints_to_json_schema(func: Callable) -> dict:
    type_hints = get_type_hints(func)
    signature = inspect.signature(func)
    func_name = getattr(func, "__name__", "operation")
    # For methods, we need to ignore the first "self" or "cls" parameter. Here we assume that if the first parameter
    # is named "self" or "cls" and has no type hint, it is an implicit receiver argument.
    first_param_name = next(iter(signature.parameters), None)
    if (
        first_param_name in {"self", "cls"}
        and signature.parameters[first_param_name].annotation == inspect.Parameter.empty
    ):
        implicit_arg_name = first_param_name
    else:
        implicit_arg_name = None
    required = []
    for param_name, param in signature.parameters.items():
        if param_name == implicit_arg_name:
            continue
        if param.annotation == inspect.Parameter.empty:
            raise TypeHintParsingException(f"Argument {param.name} is missing a type hint in function {func_name}")
        if param.default == inspect.Parameter.empty:
            required.append(param_name)

    properties = {}
    for param_name, param_type in type_hints.items():
        if param_name == implicit_arg_name:
            continue
        properties[param_name] = _parse_type_hint(param_type)

    schema = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required

    return schema