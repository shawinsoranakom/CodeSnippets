def _map(obj):
        if condition(obj):
            return fn(obj)
        elif obj is None:
            return None
        elif isinstance(obj, (list, tuple)):
            mapped = (_map(x) for x in obj)
            if hasattr(obj, "_fields"):
                # obj is namedtuple
                return type(obj)(*mapped)
            return type(obj)(mapped)
        elif isinstance(obj, dict):
            return {x: _map(obj[x]) for x in obj}
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