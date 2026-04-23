def parse_kv_cache_dtypes(node: ast.ClassDef) -> str:
    """Parse supported_kv_cache_dtypes class var or supports_kv_cache_dtype method."""
    # First try the class variable
    dtypes = _parse_list_class_var(node, "supported_kv_cache_dtypes")
    if dtypes:
        return ", ".join(dtypes)

    # Fall back to parsing the supports_kv_cache_dtype method
    # Look for `kv_cache_dtype in ["auto", "bfloat16"]` pattern
    method = find_method(node, "supports_kv_cache_dtype")
    if method:
        for n in ast.walk(method):
            if (
                isinstance(n, ast.Compare)
                and len(n.ops) == 1
                and isinstance(n.ops[0], ast.In)
                and len(n.comparators) == 1
                and isinstance(n.comparators[0], ast.List)
            ):
                dtypes = [
                    e.value
                    for e in n.comparators[0].elts
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)
                ]
                if dtypes:
                    return ", ".join(dtypes)

    return "auto"