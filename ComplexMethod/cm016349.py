def _helper(o: Any) -> Any:
        if isinstance(o, float) and (math.isinf(o) or math.isnan(o)):
            return str(o)
        if isinstance(o, list):
            return [_helper(v) for v in o]
        if isinstance(o, dict):
            return {_helper(k): _helper(v) for k, v in o.items()}
        if isinstance(o, tuple):
            return tuple(_helper(v) for v in o)
        return o