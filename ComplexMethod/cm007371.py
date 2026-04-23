def filter_fn(obj):
            if isinstance(obj, dict):
                return dict((k, filter_fn(v)) for k, v in obj.items() if not reject(k, v))
            elif isinstance(obj, (list, tuple, set, LazyList)):
                return list(map(filter_fn, obj))
            elif obj is None or any(isinstance(obj, c)
                                    for c in (compat_integer_types,
                                              (compat_str, float, bool))):
                return obj
            else:
                return repr(obj)