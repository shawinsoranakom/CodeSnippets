def clear_ignored_deprecations(*tokens: object) -> None:
    if not tokens:
        raise ValueError("Provide token or tokens returned by ignore_deprecations_from")

    new_filters = []
    old_filters = warnings._get_filters()
    endswith = tuple(rf"(?#support{id(token)})" for token in tokens)
    for action, message, category, module, lineno in old_filters:
        if action == "ignore" and category is DeprecationWarning:
            if isinstance(message, re.Pattern):
                msg = message.pattern
            else:
                msg = message or ""
            if msg.endswith(endswith):
                continue
        new_filters.append((action, message, category, module, lineno))
    if old_filters != new_filters:
        old_filters[:] = new_filters
        warnings._filters_mutated()