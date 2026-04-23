def _value_satisfies_type(value: Any, target: Any) -> bool:
    """Check whether *value* already satisfies *target*, including inner elements.

    For union types this checks each member; for generic container types it
    recursively checks that inner elements satisfy the type args (e.g. every
    element in a ``list[str]`` is a ``str``).  Returns ``False`` when uncertain
    so the caller falls through to :func:`convert`.
    """
    # typing.Any cannot be used with isinstance(); treat as always satisfied.
    if target is Any:
        return True

    origin = get_origin(target)

    if origin is Union or origin is types.UnionType:
        non_none = [a for a in get_args(target) if a is not type(None)]
        return any(_value_satisfies_type(value, member) for member in non_none)

    # Generic container type (e.g. list[str], dict[str, int])
    if origin is not None:
        # Guard: origin may not be a runtime type (e.g. Literal)
        if not isinstance(origin, type):
            return False
        if not isinstance(value, origin):
            return False
        args = get_args(target)
        if not args:
            return True
        # Check inner elements satisfy the type args
        if _is_type_or_subclass(origin, list):
            return all(_value_satisfies_type(v, args[0]) for v in value)
        if _is_type_or_subclass(origin, dict) and len(args) >= 2:
            return all(
                _value_satisfies_type(k, args[0]) and _value_satisfies_type(v, args[1])
                for k, v in value.items()
            )
        if (
            _is_type_or_subclass(origin, set) or _is_type_or_subclass(origin, frozenset)
        ) and args:
            return all(_value_satisfies_type(v, args[0]) for v in value)
        if _is_type_or_subclass(origin, tuple):
            # Homogeneous tuple[T, ...] — single type + Ellipsis
            if len(args) == 2 and args[1] is Ellipsis:
                return all(_value_satisfies_type(v, args[0]) for v in value)
            # Heterogeneous tuple[T1, T2, ...] — positional types
            if len(value) != len(args):
                return False
            return all(_value_satisfies_type(v, t) for v, t in zip(value, args))
        # Unhandled generic origin — fall through to convert()
        return False

    # Simple type (e.g. str, int)
    if isinstance(target, type):
        try:
            return isinstance(value, target)
        except TypeError:
            # TypedDict and some typing constructs don't support isinstance checks.
            # For TypedDict, check if value is a dict with the required keys.
            if isinstance(value, dict) and hasattr(target, "__required_keys__"):
                return all(k in value for k in target.__required_keys__)
            return False

    return False