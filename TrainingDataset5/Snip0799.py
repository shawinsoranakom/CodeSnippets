def _validate_list(_object: Any, var_name: str) -> None:
    if not isinstance(_object, list):
        msg = f"{var_name} must be a list"
        raise ValueError(msg)
    else:
        for x in _object:
            if not isinstance(x, str):
                msg = f"{var_name} must be a list of strings"
                raise ValueError(msg)
