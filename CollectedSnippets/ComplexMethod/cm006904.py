def prepare_global_scope(module):
    """Prepares the global scope with necessary imports from the provided code module.

    Args:
        module: AST parsed module

    Returns:
        Dictionary representing the global scope with imported modules

    Raises:
        ModuleNotFoundError: If a module is not found in the code
    """
    exec_globals = globals().copy()
    imports = []
    import_froms = []
    definitions = []

    for node in module.body:
        if isinstance(node, ast.Import):
            imports.append(node)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            import_froms.append(node)
        elif isinstance(node, ast.ClassDef | ast.FunctionDef | ast.Assign | ast.AnnAssign):
            definitions.append(node)

    for node in imports:
        for alias in node.names:
            module_name = alias.name

            module_obj = None
            for name in _get_module_fallbacks(module_name):
                try:
                    module_obj = importlib.import_module(name)
                    break
                except ModuleNotFoundError:
                    continue

            if module_obj is None:
                if sys.platform == "win32":
                    # Some C-extension packages (e.g. jq) have no Windows
                    # wheels.  Insert a lazy placeholder so that class creation
                    # succeeds and update_build_config can run.  Any real usage
                    # of the module at runtime will raise ModuleNotFoundError.
                    variable_name = alias.asname or module_name.split(".")[0]
                    exec_globals[variable_name] = _MissingModulePlaceholder(module_name)
                    logger.debug("Module '%s' unavailable on Windows — inserted placeholder", module_name)
                    continue
                # On other platforms the package should be installable, so
                # raise to surface the real error.
                module_obj = importlib.import_module(module_name)

            # Determine the variable name
            if alias.asname:
                # For aliased imports like "import yfinance as yf", use the imported module directly
                variable_name = alias.asname
                exec_globals[variable_name] = module_obj
            else:
                # For dotted imports like "urllib.request", set the variable to the top-level package.
                # importlib.import_module returns the *leaf* module, but Python's import statement
                # binds the top-level package name. Retrieve it from sys.modules instead.
                variable_name = module_name.split(".")[0]
                exec_globals[variable_name] = sys.modules.get(variable_name, module_obj)

    for node in import_froms:
        module_names_to_try = _get_module_fallbacks(node.module)

        success = False
        last_error = None

        for module_name in module_names_to_try:
            try:
                imported_module = _import_module_with_warnings(module_name)
                _handle_module_attributes(imported_module, node, module_name, exec_globals)

                success = True
                break

            except ModuleNotFoundError as e:
                last_error = e
                continue

        if not success:
            # Re-raise the last error to preserve the actual missing module information
            if last_error:
                raise last_error
            msg = f"Module {node.module} not found. Please install it and try again"
            raise ModuleNotFoundError(msg)

    if definitions:
        combined_module = ast.Module(body=definitions, type_ignores=[])
        compiled_code = compile(combined_module, "<string>", "exec")
        exec(compiled_code, exec_globals)

    return exec_globals