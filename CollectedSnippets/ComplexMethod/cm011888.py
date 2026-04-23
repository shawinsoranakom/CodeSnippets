def process_arg(
        x: T, ignore_types_override: Sequence[type[Any]] | None = None
    ) -> T | KeywordArg | Ignored:
        current_ignore_types = (
            ignore_types_override if ignore_types_override is not None else ignore_types
        )
        if isinstance(x, (float, int)) and x in inv_scalar_workaround:
            return KeywordArg(inv_scalar_workaround[x])
        if type(x) in current_ignore_types:
            return Ignored()
        if isinstance(x, list) and all(isinstance(y, Ignored) for y in x) and x:
            return Ignored()
        return x