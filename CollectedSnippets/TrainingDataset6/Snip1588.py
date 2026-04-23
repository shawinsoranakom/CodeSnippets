def get_cached_model_fields(model: type[BaseModel]) -> list[ModelField]:
    return get_model_fields(model)