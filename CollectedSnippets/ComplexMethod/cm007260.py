def post_process_type(type_):
    """Process the return type of a function.

    Args:
        type_ (Any): The return type of the function.

    Returns:
        Union[List[Any], Any]: The processed return type.
    """
    if hasattr(type_, "__origin__") and type_.__origin__ in {list, list, SequenceABC}:
        type_ = extract_inner_type_from_generic_alias(type_)

    # If the return type is not a Union, then we just return it as a list
    inner_type = type_[0] if isinstance(type_, list) else type_
    if (not hasattr(inner_type, "__origin__") or inner_type.__origin__ != Union) and (
        not hasattr(inner_type, "__class__") or inner_type.__class__.__name__ != "UnionType"
    ):
        return type_ if isinstance(type_, list) else [type_]
    # If the return type is a Union, then we need to parse it
    type_ = extract_union_types_from_generic_alias(type_)
    type_ = set(chain.from_iterable([post_process_type(t) for t in type_]))
    return list(type_)