def _find_tensors(obj):
    r"""Recursively find all tensors contained in the specified object."""
    if RPC_AVAILABLE and isinstance(obj, RRef):
        # If the current node is the owner of the RRef, unwrap it and try to
        # find Tensors.
        # TODO: Expand to remote RRefs.
        if obj.is_owner():
            return _find_tensors(obj.local_value())
    if isinstance(obj, torch.Tensor):
        return [obj]
    if isinstance(obj, (list, tuple)):
        return itertools.chain.from_iterable(map(_find_tensors, obj))
    if isinstance(obj, dict):
        return itertools.chain.from_iterable(map(_find_tensors, obj.values()))
    if is_dataclass(obj):
        return itertools.chain.from_iterable(
            map(_find_tensors, (getattr(obj, f.name) for f in fields(obj)))
        )

    return []