def get_greatest_upper_bound(type1: Any, type2: Any) -> Any:
    """
    Get the most precise type that's consistent with the given types
    """
    if type1 == Dyn:
        return type2
    elif type2 == Dyn:
        return type1
    elif isinstance(type1, TensorType) and isinstance(type2, TensorType):
        if not is_consistent(type1, type2):
            raise TypeError(f"Inconsistent types {type1}, {type2}")
        gub = [
            t1 if is_more_precise(t1, t2) else t2
            for (t1, t2) in zip(type1.__args__, type2.__args__)
        ]
        return TensorType(tuple(gub))