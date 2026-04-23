def get_decorator_details(function) -> Decorator | None:
    """Extract decorators and their arguments from a function."""
    source = inspect.getsource(function)
    parsed_source = parse(source)

    if isinstance(parsed_source.body[0], (FunctionDef, AsyncFunctionDef)):
        func_def = parsed_source.body[0]
        for decorator in func_def.decorator_list:
            if isinstance(decorator, Call):
                name = (
                    decorator.func.id
                    if isinstance(decorator.func, Name)
                    else unparse(decorator.func)
                )
                args = {i: unparse(arg) for i, arg in enumerate(decorator.args)}
                kwargs = {kw.arg: unparse(kw.value) for kw in decorator.keywords}
            else:
                name = (
                    decorator.id if isinstance(decorator, Name) else unparse(decorator)
                )
        return Decorator(name, args, kwargs)
    return None