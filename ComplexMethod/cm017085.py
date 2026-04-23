def annotation_is_pydantic_v1(annotation: Any) -> bool:
    if is_pydantic_v1_model_class(annotation):
        return True
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        for arg in get_args(annotation):
            if is_pydantic_v1_model_class(arg):
                return True
    if field_annotation_is_sequence(annotation):
        for sub_annotation in get_args(annotation):
            if annotation_is_pydantic_v1(sub_annotation):
                return True
    return False