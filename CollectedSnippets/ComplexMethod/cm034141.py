def _extract_type(target_type: type, of_type: type) -> type:
    """Return `of_type` from `target_type`, where `target_type` may be a union."""
    origin_type = t.get_origin(target_type)

    if origin_type is of_type:  # pylint: disable=unidiomatic-typecheck
        return target_type

    if origin_type is t.Union or (_union_type and isinstance(target_type, _union_type)):
        args = t.get_args(target_type)
        extracted_types = [arg for arg in args if type(arg) is of_type or t.get_origin(arg) is of_type]  # pylint: disable=unidiomatic-typecheck
        (extracted_type,) = extracted_types
        return extracted_type

    raise NotImplementedError(f'{target_type} is not supported')