def _calls_service_registration(
    async_setup_entry_function: ast.AsyncFunctionDef,
) -> bool:
    """Check if there are calls to service registration."""
    for node in ast.walk(async_setup_entry_function):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue

        if node.func.attr == "async_register_entity_service":
            return True

        if (
            isinstance(node.func.value, ast.Attribute)
            and isinstance(node.func.value.value, ast.Name)
            and node.func.value.value.id == "hass"
            and node.func.value.attr == "services"
            and node.func.attr in {"async_register", "register"}
        ):
            return True

    return False