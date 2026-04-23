def scatter_map(obj):
        if isinstance(obj, torch.Tensor):
            return Scatter.apply(target_gpus, None, dim, obj)
        if _is_namedtuple(obj):
            return [
                type(obj)(*args)
                # pyrefly: ignore [bad-argument-type, no-matching-overload]
                for args in zip(*map(scatter_map, obj), strict=False)
            ]
        if isinstance(obj, tuple) and len(obj) > 0:
            # pyrefly: ignore [bad-argument-type, no-matching-overload]
            return list(zip(*map(scatter_map, obj), strict=False))
        if isinstance(obj, list) and len(obj) > 0:
            # pyrefly: ignore [bad-argument-type, no-matching-overload]
            return [list(i) for i in zip(*map(scatter_map, obj), strict=False)]
        if isinstance(obj, dict) and len(obj) > 0:
            return [
                type(obj)(i)
                # pyrefly: ignore [bad-argument-type, no-matching-overload]
                for i in zip(*map(scatter_map, obj.items()), strict=False)
            ]
        return [obj for _ in target_gpus]