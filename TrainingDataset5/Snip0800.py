def _validate_nested_dict(_object: Any, var_name: str) -> None:
    _validate_dict(_object, var_name, dict)
    for x in _object.values():
        _validate_dict(x, var_name, float, True)
