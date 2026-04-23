def is_union_of_base_models(field_type: Any) -> bool:
    """Check if field type is a Union where all members are BaseModel subclasses."""
    from fastapi.types import UnionType

    origin = get_origin(field_type)

    # Check if it's a Union type (covers both typing.Union and types.UnionType in Python 3.10+)
    if origin is not Union and origin is not UnionType:
        return False

    union_args = get_args(field_type)

    for arg in union_args:
        if not lenient_issubclass(arg, BaseModel):
            return False

    return True