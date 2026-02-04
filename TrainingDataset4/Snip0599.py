def _is_safe_type_alias(node: ast.Assign) -> bool:
    """Check if an assignment is a safe type alias that shouldn't be stubbed.

    Safe types are:
    - Literal types (don't cause type budget issues)
    - Simple type references (SortMode, SortOrder, etc.)
    - TypeVar definitions
    """
    if not node.value:
        return False

    # Check if it's a Subscript (like Literal[...], Union[...], TypeVar[...])
    if isinstance(node.value, ast.Subscript):
        # Get the base type name
        if isinstance(node.value.value, ast.Name):
            base_name = node.value.value.id
            # Literal types are safe
            if base_name == "Literal":
                return True
            # TypeVar is safe
            if base_name == "TypeVar":
                return True
        elif isinstance(node.value.value, ast.Attribute):
            # Handle typing_extensions.Literal etc.
            if node.value.value.attr == "Literal":
                return True

    # Check if it's a simple Name reference (like SortMode = _types.SortMode)
    if isinstance(node.value, ast.Attribute):
        return True

    # Check if it's a Call (like TypeVar(...))
    if isinstance(node.value, ast.Call):
        if isinstance(node.value.func, ast.Name):
            if node.value.func.id == "TypeVar":
                return True

    return False
