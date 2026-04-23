def _strip_annotations(t):
    """Strip the annotations from a given type."""
    if isinstance(t, _AnnotatedAlias):
        return _strip_annotations(t.__origin__)
    if hasattr(t, "__origin__") and t.__origin__ in (Required, NotRequired, ReadOnly):
        return _strip_annotations(t.__args__[0])
    if isinstance(t, _GenericAlias):
        stripped_args = tuple(_strip_annotations(a) for a in t.__args__)
        if stripped_args == t.__args__:
            return t
        return t.copy_with(stripped_args)
    if isinstance(t, GenericAlias):
        stripped_args = tuple(_strip_annotations(a) for a in t.__args__)
        if stripped_args == t.__args__:
            return t
        return _rebuild_generic_alias(t, stripped_args)
    if isinstance(t, Union):
        stripped_args = tuple(_strip_annotations(a) for a in t.__args__)
        if stripped_args == t.__args__:
            return t
        return functools.reduce(operator.or_, stripped_args)

    return t