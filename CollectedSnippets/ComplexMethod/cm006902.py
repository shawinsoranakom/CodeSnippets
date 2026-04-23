def create_function(code, function_name):
    if not hasattr(ast, "TypeIgnore"):

        class TypeIgnore(ast.AST):
            _fields = ()

        ast.TypeIgnore = TypeIgnore

    module = ast.parse(code)
    exec_globals = globals().copy()

    for node in module.body:
        if isinstance(node, ast.Import | ast.ImportFrom):
            for alias in node.names:
                try:
                    if isinstance(node, ast.ImportFrom):
                        module_name = node.module
                        exec_globals[alias.asname or alias.name] = getattr(
                            importlib.import_module(module_name), alias.name
                        )
                    else:
                        module_name = alias.name
                        imported = importlib.import_module(module_name)
                        if alias.asname:
                            exec_globals[alias.asname] = imported
                        else:
                            top_level = module_name.split(".")[0]
                            exec_globals[top_level] = sys.modules.get(top_level, imported)
                except ModuleNotFoundError as e:
                    msg = f"Module {alias.name} not found. Please install it and try again."
                    raise ModuleNotFoundError(msg) from e

    function_code = next(
        node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == function_name
    )
    function_code.parent = None
    code_obj = compile(ast.Module(body=[function_code], type_ignores=[]), "<string>", "exec")
    exec_locals = dict(locals())
    with contextlib.suppress(Exception):
        exec(code_obj, exec_globals, exec_locals)
    exec_globals[function_name] = exec_locals[function_name]

    # Return a function that imports necessary modules and calls the target function
    def wrapped_function(*args, **kwargs):
        for module_name, module in exec_globals.items():
            if isinstance(module, type(importlib)):
                globals()[module_name] = module

        return exec_globals[function_name](*args, **kwargs)

    return wrapped_function