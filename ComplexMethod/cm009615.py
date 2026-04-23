def _replace_type_vars(
    type_: type | TypeVar,
    generic_map: dict[TypeVar, type] | None = None,
    *,
    default_to_bound: bool = True,
) -> type | TypeVar:
    """Replace `TypeVar`s in a type annotation with concrete types.

    Args:
        type_: The type annotation to process.
        generic_map: Mapping of `TypeVar`s to concrete types.
        default_to_bound: Whether to use `TypeVar` bounds as defaults.

    Returns:
        The type with `TypeVar`s replaced.
    """
    generic_map = generic_map or {}
    if isinstance(type_, TypeVar):
        if type_ in generic_map:
            return generic_map[type_]
        if default_to_bound:
            return type_.__bound__ if type_.__bound__ is not None else Any
        return type_
    if (origin := get_origin(type_)) and (args := get_args(type_)):
        new_args = tuple(
            _replace_type_vars(arg, generic_map, default_to_bound=default_to_bound)
            for arg in args
        )
        return cast("type", _py_38_safe_origin(origin)[new_args])  # type: ignore[index]
    return type_