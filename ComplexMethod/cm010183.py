def _dataclass_to_dict(obj):
    if isinstance(obj, _Union):
        return {obj.type: _dataclass_to_dict(obj.value)}
    elif dataclasses.is_dataclass(obj):
        return {
            f.name: _dataclass_to_dict(getattr(obj, f.name))
            for f in dataclasses.fields(obj)
        }
    elif isinstance(obj, list):
        return [_dataclass_to_dict(x) for x in obj]
    elif isinstance(obj, tuple):
        return tuple(_dataclass_to_dict(x) for x in obj)
    elif isinstance(obj, dict):
        return {k: _dataclass_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, float):
        if obj == math.inf:
            return "Infinity"
        elif obj == -math.inf:
            return "-Infinity"
        elif math.isnan(obj):
            return "NaN"
        else:
            return obj
    else:
        return obj