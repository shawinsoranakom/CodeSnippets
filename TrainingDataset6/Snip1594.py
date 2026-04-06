def get_flat_models_from_fields(
    fields: Sequence[ModelField], known_models: TypeModelSet
) -> TypeModelSet:
    for field in fields:
        get_flat_models_from_field(field, known_models=known_models)
    return known_models