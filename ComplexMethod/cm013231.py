def to_gpu(obj, type_map=None):
    if type_map is None:
        type_map = {}
    if isinstance(obj, torch.Tensor):
        if not obj.is_leaf:
            raise AssertionError("expected obj to be a leaf tensor")
        t = type_map.get(obj.dtype, obj.dtype)
        with torch.no_grad():
            res = obj.to(dtype=t, device="cuda", copy=True)
            res.requires_grad = obj.requires_grad
        return res
    elif torch.is_storage(obj):
        return obj.new().resize_(obj.size()).copy_(obj)  # type: ignore[attr-defined, union-attr]
    elif isinstance(obj, list):
        return [to_gpu(o, type_map) for o in obj]
    elif isinstance(obj, tuple):
        return tuple(to_gpu(o, type_map) for o in obj)
    else:
        return deepcopy(obj)