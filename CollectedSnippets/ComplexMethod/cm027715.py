def _check_typed_config_entry(integration: Integration) -> list[str]:
    """Ensure integration uses CustomConfigEntry type annotation."""
    errors: list[str] = []
    # Check body level function annotations
    for file, functions in _FUNCTIONS.items():
        module_file = integration.path / f"{file}.py"
        if not module_file.exists():
            continue
        module = ast_parse_module(module_file)
        for function, position in functions.items():
            if not (async_function := _get_async_function(module, function)):
                continue
            if error := _check_function_annotation(async_function, position):
                errors.append(f"{error} in {module_file}")

    # Check config_flow annotations
    config_flow_file = integration.path / "config_flow.py"
    config_flow = ast_parse_module(config_flow_file)
    for node in config_flow.body:
        if not isinstance(node, ast.ClassDef):
            continue
        if any(
            isinstance(async_function, ast.FunctionDef)
            and async_function.name == "async_get_options_flow"
            and (error := _check_function_annotation(async_function, 1))
            for async_function in node.body
        ):
            errors.append(f"{error} in {config_flow_file}")

    return errors