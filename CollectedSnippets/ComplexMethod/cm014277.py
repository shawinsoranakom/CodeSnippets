def map_aggregate(a: Any, fn: Callable[[Any], Any]) -> Any:
    result: Any
    if isinstance(a, tuple):
        it = (map_aggregate(elem, fn) for elem in a)
        # Support NamedTuple (if it has `_fields`) by repacking into original type.
        result = type(a)(*it) if hasattr(a, "_fields") else tuple(it)
    elif isinstance(a, list):
        result = immutable_list([map_aggregate(elem, fn) for elem in a])
    elif isinstance(a, dict):
        result = immutable_dict([(k, map_aggregate(v, fn)) for k, v in a.items()])
    elif isinstance(a, slice):
        result = slice(
            map_aggregate(a.start, fn),
            map_aggregate(a.stop, fn),
            map_aggregate(a.step, fn),
        )
    else:
        result = fn(a)
    return result