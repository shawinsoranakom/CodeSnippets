def _resolve_expected_type(annotation: Any) -> type | None:
    """Resolve the effective expected type from a Pydantic field annotation.

    Handles Union, UnionType (X | None), list, list[X]. Returns the primary
    type (dict, list, int, float, bool, str) or None if not one we normalize.
    """
    ann = annotation
    origin = get_origin(ann)
    if origin is UnionType or origin is Union:
        args = get_args(ann)
        non_none = [a for a in args if a is not type(None)]
        if non_none:
            ann = non_none[0]
            origin = get_origin(ann)
    if origin is list or ann is list:
        return list
    if origin is dict or ann is dict:
        return dict
    if ann in (int, float, bool, str):
        return ann
    return None