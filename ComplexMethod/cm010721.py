def tuple_to_list(tuple_type: type[tuple]) -> type[list]:
    """
    Convert `tuple_type` into a list type with the same type arguments. Assumes that `tuple_type` is typing.Tuple type.
    """
    type_args = getattr(tuple_type, "__args__", None)
    # Account for different python versions, e.g. python 3.8 would give ()
    # but python 3.12 would give None.
    if (
        tuple_type is typing.Tuple  # noqa: UP006
        or tuple_type is tuple
        or type_args == ()
        or type_args is None
    ):
        # Handle the case of an empty tuple type
        return list
    elif len(type_args) == 1:
        # General case: create a List with the same type arguments
        return list[type_args[0]]  # type: ignore[valid-type]
    elif len(type_args) == 2 and type_args[1] is Ellipsis:
        return list[type_args[0]]  # type: ignore[valid-type]
    else:
        return list[typing.Union[tuple(type_args)]]