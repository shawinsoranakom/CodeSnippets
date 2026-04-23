def substitute_solution_one_type(mapping: dict[object, object], t: object) -> Any:
    """
    Apply the most general unifier to a type
    """
    if isinstance(t, Var):
        if t in mapping:
            return mapping[t]
        else:
            return t

    elif isinstance(t, TensorType):
        new_type = []
        for typ in t.__args__:
            if typ in mapping:
                new_type.append(mapping[typ])
            else:
                new_type.append(typ)
        return TensorType(tuple(new_type))

    elif isinstance(t, list):
        new_type = []
        for typ in t:
            new_type.append(substitute_solution_one_type(mapping, typ))
        return new_type

    elif isinstance(t, tuple):
        new_type = []
        for typ in t:
            new_type.append(substitute_solution_one_type(mapping, typ))
        return tuple(new_type)

    else:
        return t