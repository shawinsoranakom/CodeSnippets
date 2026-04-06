def get_model_name_map(unique_models: TypeModelSet) -> dict[TypeModelOrEnum, str]:
    name_model_map = {}
    for model in unique_models:
        model_name = normalize_name(model.__name__)
        name_model_map[model_name] = model
    return {v: k for k, v in name_model_map.items()}