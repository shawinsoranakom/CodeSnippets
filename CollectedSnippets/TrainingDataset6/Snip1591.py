def get_flat_models_from_model(
    model: type["BaseModel"], known_models: TypeModelSet | None = None
) -> TypeModelSet:
    known_models = known_models or set()
    fields = get_model_fields(model)
    get_flat_models_from_fields(fields, known_models=known_models)
    return known_models