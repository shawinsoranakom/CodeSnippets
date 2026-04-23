def get_flat_models_from_field(
    field: ModelField, known_models: TypeModelSet
) -> TypeModelSet:
    field_type = field.field_info.annotation
    if lenient_issubclass(field_type, BaseModel):
        if field_type in known_models:
            return known_models
        known_models.add(field_type)
        get_flat_models_from_model(field_type, known_models=known_models)
    elif lenient_issubclass(field_type, Enum):
        known_models.add(field_type)
    else:
        get_flat_models_from_annotation(field_type, known_models=known_models)
    return known_models