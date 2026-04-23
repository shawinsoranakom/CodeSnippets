def _signatures_match(
    schema_a: torch._C.FunctionSchema,
    schema_b: torch._C.FunctionSchema,
) -> bool:
    """Compare two schemas by their non-mutable arguments (name, type, default value)."""
    non_mutable_args_a = [arg for arg in schema_a.arguments if not _is_mutable_arg(arg)]
    non_mutable_args_b = [arg for arg in schema_b.arguments if not _is_mutable_arg(arg)]
    if len(non_mutable_args_a) != len(non_mutable_args_b):
        return False
    for a, b in zip(non_mutable_args_a, non_mutable_args_b):
        if a.name != b.name:
            return False
        if str(a.type) != str(b.type):
            return False
        if a.default_value != b.default_value:
            return False
    return True