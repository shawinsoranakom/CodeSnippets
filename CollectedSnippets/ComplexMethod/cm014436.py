def issubinstance(data, data_type):
    if not issubtype(type(data), data_type, recursive=False):
        return False

    # In Python-3.9 typing library __args__ attribute is not defined for untyped generics
    dt_args = getattr(data_type, "__args__", None)
    if isinstance(data, tuple):
        if dt_args is None or len(dt_args) == 0:
            return True
        if len(dt_args) != len(data):
            return False
        return all(issubinstance(d, t) for d, t in zip(data, dt_args, strict=True))
    elif isinstance(data, (list, set)):
        if dt_args is None or len(dt_args) == 0:
            return True
        t = dt_args[0]
        return all(issubinstance(d, t) for d in data)
    elif isinstance(data, dict):
        if dt_args is None or len(dt_args) == 0:
            return True
        kt, vt = dt_args
        return all(
            issubinstance(k, kt) and issubinstance(v, vt) for k, v in data.items()
        )

    return True