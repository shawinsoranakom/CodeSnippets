def convert_to_typed_dict(typed_dict: type[T], obj: dict, strict: bool = False) -> T:
    """
    Converts the given object to the given typed dict (by calling the type constructors).
    Limitations:
    - This does not work for ForwardRefs (type refs in quotes).
    - If a type is a Union, the first type is used for the conversion.
    - The conversion fails for types which cannot be instantiated with the constructor.

    :param typed_dict: to convert the given object to
    :param obj: object to convert matching keys to the types defined in the typed dict
    :param strict: True if a TypeError should be raised in case the conversion fails
    :return: obj converted to the typed dict T
    """
    result = cast(T, select_from_typed_dict(typed_dict, obj, filter=True))
    for key, key_type in typed_dict.__annotations__.items():
        if key in result:
            # If it's a Union, or optional, we extract the first type argument
            if get_origin(key_type) in [Union, Optional]:
                key_type = get_args(key_type)[0]
            # Use duck-typing to check if the dict is a typed dict
            if hasattr(key_type, "__required_keys__") and hasattr(key_type, "__optional_keys__"):
                result[key] = convert_to_typed_dict(key_type, result[key])
            else:
                # Otherwise, we call the type's constructor (on a best-effort basis)
                try:
                    result[key] = key_type(result[key])
                except TypeError as e:
                    if strict:
                        raise e
                    else:
                        LOG.debug("Could not convert %s to %s.", key, key_type)
    return result