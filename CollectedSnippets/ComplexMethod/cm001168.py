def _try_convert(value: Any, target_type: Any, raise_on_mismatch: bool) -> Any:
    origin = get_origin(target_type)
    args = get_args(target_type)

    # Handle Union types (including Optional which is Union[T, None])
    if origin is Union or origin is types.UnionType:
        # Handle None values for Optional types
        if value is None:
            if type(None) in args:
                return None
            elif raise_on_mismatch:
                raise TypeError(f"Value {value} is not of expected type {target_type}")
            else:
                return value

        # Try to convert to each type in the union, excluding None
        non_none_types = [arg for arg in args if arg is not type(None)]

        # Try each type in the union, using the original raise_on_mismatch behavior
        for arg_type in non_none_types:
            try:
                return _try_convert(value, arg_type, raise_on_mismatch)
            except (TypeError, ValueError, ConversionError):
                continue

        # If no conversion succeeded
        if raise_on_mismatch:
            raise TypeError(f"Value {value} is not of expected type {target_type}")
        else:
            return value

    if origin is None:
        origin = target_type
    # Early return for unsupported types (skip subclasses of supported types)
    supported_types = [list, dict, tuple, str, set, int, float, bool]
    if origin not in supported_types and not (
        isinstance(origin, type) and any(issubclass(origin, t) for t in supported_types)
    ):
        return value

    # Handle the case when value is already of the target type
    if isinstance(value, origin):
        if not args:
            return value
        else:
            # Need to convert elements
            if origin is list:
                return [convert(v, args[0]) for v in value]
            elif origin is tuple:
                # Tuples can have multiple types
                if len(args) == 1:
                    return tuple(convert(v, args[0]) for v in value)
                else:
                    return tuple(convert(v, t) for v, t in zip(value, args))
            elif origin is dict:
                key_type, val_type = args
                return {
                    convert(k, key_type): convert(v, val_type) for k, v in value.items()
                }
            elif origin is set:
                return {convert(v, args[0]) for v in value}
            else:
                return value
    elif raise_on_mismatch:
        raise TypeError(f"Value {value} is not of expected type {target_type}")
    else:
        # Need to convert value to the origin type
        if _is_type_or_subclass(origin, list):
            converted_list = __convert_list(value)
            if args:
                converted_list = [convert(v, args[0]) for v in converted_list]
            return origin(converted_list) if origin is not list else converted_list
        elif _is_type_or_subclass(origin, dict):
            converted_dict = __convert_dict(value)
            if args:
                key_type, val_type = args
                converted_dict = {
                    convert(k, key_type): convert(v, val_type)
                    for k, v in converted_dict.items()
                }
            return origin(converted_dict) if origin is not dict else converted_dict
        elif _is_type_or_subclass(origin, tuple):
            converted_tuple = __convert_tuple(value)
            if args:
                if len(args) == 1:
                    converted_tuple = tuple(
                        convert(v, args[0]) for v in converted_tuple
                    )
                else:
                    converted_tuple = tuple(
                        convert(v, t) for v, t in zip(converted_tuple, args)
                    )
            return origin(converted_tuple) if origin is not tuple else converted_tuple
        elif _is_type_or_subclass(origin, str):
            converted_str = __convert_str(value)
            return origin(converted_str) if origin is not str else converted_str
        elif _is_type_or_subclass(origin, set):
            value = __convert_set(value)
            if args:
                return {convert(v, args[0]) for v in value}
            else:
                return value
        elif _is_type_or_subclass(origin, bool):
            return __convert_bool(value)
        elif _is_type_or_subclass(origin, int):
            return __convert_num(value, int)
        elif _is_type_or_subclass(origin, float):
            return __convert_num(value, float)
        else:
            return value