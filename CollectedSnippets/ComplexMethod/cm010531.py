def _iter(obj):
        if conversion is not None:
            obj = conversion(obj)
        if condition(obj):
            yield obj
        elif obj is None:
            return
        elif isinstance(obj, (list, tuple)):
            for o in obj:
                yield from _iter(o)
        elif isinstance(obj, dict):
            # We only accept primitive key types, so we needn't inspect them
            for o in obj.values():
                yield from _iter(o)
        elif allow_unknown:
            yield obj
        else:
            raise ValueError(
                "Auto nesting doesn't know how to process "
                "an input object of type "
                + torch.typename(obj)
                + (
                    ". Accepted types: " + condition_msg + ", or lists/tuples of them"
                    if condition_msg
                    else ""
                )
            )