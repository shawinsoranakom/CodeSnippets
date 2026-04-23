def filter_fn(obj):
            if isinstance(obj, dict):
                return {k: filter_fn(v) for k, v in obj.items() if not reject(k, v)}
            elif isinstance(obj, (list, tuple, set, LazyList)):
                return list(map(filter_fn, obj))
            elif isinstance(obj, ImpersonateTarget):
                return str(obj)
            elif obj is None or isinstance(obj, (str, int, float, bool)):
                return obj
            else:
                return repr(obj)