def _lookup_code(entry: _DynamoCodeCacheEntry) -> types.CodeType:
    assert len(entry.function_names) == 1
    fn: Any = sys.modules[entry.python_module]
    parts = entry.function_names[0].split(".")
    for part in parts:
        fn = getattr(fn, part)
    if entry.code_source:
        parts = entry.code_source.split(".")
        for part in parts:
            if part.endswith("]"):
                index_begin = part.rfind("[")
                assert isinstance(index_begin, int) and index_begin >= 0
                attr = getattr(fn, part[:index_begin], None)
                if attr is None:
                    raise PackageError(f"Cannot find source for code entry {entry}")
                fn = attr[ast.literal_eval(part[index_begin + 1 : -1])]
            else:
                fn = getattr(fn, part)
    else:
        raise PackageError(f"Cannot find source for code entry {entry}")
    assert isinstance(fn, types.CodeType)
    return fn