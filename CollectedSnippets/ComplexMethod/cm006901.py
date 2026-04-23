def execute_function(code, function_name, *args, **kwargs):
    add_type_ignores()

    module = ast.parse(code)
    exec_globals = globals().copy()

    for node in module.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                try:
                    imported = importlib.import_module(alias.name)
                    if alias.asname:
                        variable_name = alias.asname
                        exec_globals[variable_name] = imported
                    else:
                        variable_name = alias.name.split(".")[0]
                        exec_globals[variable_name] = sys.modules.get(variable_name, imported)
                except ModuleNotFoundError as e:
                    msg = f"Module {alias.name} not found. Please install it and try again."
                    raise ModuleNotFoundError(msg) from e

    function_code = next(
        node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == function_name
    )
    function_code.parent = None
    code_obj = compile(ast.Module(body=[function_code], type_ignores=[]), "<string>", "exec")
    exec_locals = dict(locals())
    try:
        exec(code_obj, exec_globals, exec_locals)
    except Exception as exc:
        msg = "Function string does not contain a function"
        raise ValueError(msg) from exc

    # Add the function to the exec_globals dictionary
    exec_globals[function_name] = exec_locals[function_name]

    return exec_globals[function_name](*args, **kwargs)