def get_flat_models_from_annotation(
    annotation: Any, known_models: TypeModelSet
) -> TypeModelSet:
    origin = get_origin(annotation)
    if origin is not None:
        for arg in get_args(annotation):
            if lenient_issubclass(arg, (BaseModel, Enum)):
                if arg not in known_models:
                    known_models.add(arg)  # type: ignore[arg-type]  # ty: ignore[unused-ignore-comment]
                    if lenient_issubclass(arg, BaseModel):
                        get_flat_models_from_model(arg, known_models=known_models)
            else:
                get_flat_models_from_annotation(arg, known_models=known_models)
    return known_models