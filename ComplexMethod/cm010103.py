def container_checker(obj, target_type) -> bool:
    origin_type = get_origin(target_type)
    check_args_exist(target_type)
    if origin_type is None:
        return False
    elif origin_type is list or origin_type is typing.List:  # noqa: UP006
        check_empty_containers(obj)
        if not isinstance(obj, list):
            return False
        arg_type = get_args(target_type)[0]
        arg_origin = get_origin(arg_type)
        for el in obj:
            # check if nested container, ex: List[List[str]]
            if arg_origin:  # processes nested container, ex: List[List[str]]
                if not container_checker(el, arg_type):
                    return False
            elif not isinstance(el, arg_type):
                return False
        return True
    elif origin_type is typing.Dict or origin_type is dict:  # noqa: UP006
        check_empty_containers(obj)
        if not isinstance(obj, dict):
            return False
        key_type = get_args(target_type)[0]
        val_type = get_args(target_type)[1]
        for key, val in obj.items():
            # check if keys are of right type
            if not isinstance(key, key_type):
                return False
            val_origin = get_origin(val_type)
            if val_origin:
                if not container_checker(val, val_type):
                    return False
            elif not isinstance(val, val_type):
                return False
        return True
    elif origin_type is typing.Tuple or origin_type is tuple:  # noqa: UP006
        check_empty_containers(obj)
        if not isinstance(obj, tuple):
            return False
        arg_types = get_args(target_type)
        if len(obj) != len(arg_types):
            return False
        for el, el_type in zip(obj, arg_types):
            el_origin = get_origin(el_type)
            if el_origin:
                if not container_checker(el, el_type):
                    return False
            elif not isinstance(el, el_type):
                return False
        return True
    elif origin_type is Union or issubclass(
        origin_type,
        BuiltinUnionType,
    ):  # also handles Optional
        if obj is None:  # check before recursion because None is always fine
            return True
        inner_types = get_args(target_type)
        for t in inner_types:
            t_origin = get_origin(t)
            if t_origin:
                return container_checker(obj, t)
            elif isinstance(obj, t):
                return True
    return False