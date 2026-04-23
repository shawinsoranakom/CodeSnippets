def find_mismatched_vars(
    var: Any, types: type | tuple[type, ...], allow_none: bool = False
) -> set[VariableTracker]:
    """
    Recursively finds variables whose type is not an instance of the specified types.
    Args:
        var: The variable to check.
        types: A tuple of allowed types.
        allow_none (bool): Whether to allow None values. Defaults to False.
    Returns:
        A set of variables whose type is not an instance of the specified types.
    """
    mismatched_vars = set()
    if isinstance(var, (list, tuple)):
        for item in var:
            mismatched_vars.update(find_mismatched_vars(item, types, allow_none))
    elif isinstance(var, (TupleVariable, ListVariable)):
        for item in var.items:
            mismatched_vars.update(find_mismatched_vars(item, types, allow_none))
    elif isinstance(var, ConstDictVariable):
        for value in var.items.values():
            mismatched_vars.update(find_mismatched_vars(value, types, allow_none))
    elif isinstance(var, SetVariable):
        for key in var.items:
            mismatched_vars.update(find_mismatched_vars(key.vt, types, allow_none))
    else:
        if not isinstance(var, types) and not (allow_none and var.is_constant_none()):
            mismatched_vars.add(var)
    return mismatched_vars