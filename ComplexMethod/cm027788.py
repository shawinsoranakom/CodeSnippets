def hash_obj(obj: object) -> int:
    if isinstance(obj, dict):
        return hash(tuple(sorted([
            (hash_obj(k), hash_obj(v)) for k, v in obj.items()
        ])))

    if isinstance(obj, set):
        return hash(tuple(sorted(hash_obj(e) for e in obj)))

    if isinstance(obj, (tuple, list)):
        return hash(tuple(hash_obj(e) for e in obj))

    if isinstance(obj, Color):
        return hash(obj.get_rgb())

    return hash(obj)