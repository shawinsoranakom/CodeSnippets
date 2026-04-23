def normalize_count_iter(count_iter: Iterator[Any]) -> tuple[Any, Any]:
    try:
        _, args = count_iter.__reduce__()
    except TypeError:
        # Python 3.14 no longer pickles itertools.count, so fall back to the
        # repr and only recover literal arguments. Non-literal arguments still
        # fall back to user-defined handling via the NotImplemented sentinel.
        import ast

        count_repr = repr(count_iter)
        if not count_repr.startswith("count(") or not count_repr.endswith(")"):
            return (NotImplemented, NotImplemented)
        try:
            args = ast.literal_eval(f"({count_repr[6:-1]},)")
        except (SyntaxError, ValueError):
            return (NotImplemented, NotImplemented)
        if not isinstance(args, tuple) or not 1 <= len(args) <= 2:
            return (NotImplemented, NotImplemented)
    if len(args) == 1:
        return (args[0], 1)
    return (args[0], args[1])