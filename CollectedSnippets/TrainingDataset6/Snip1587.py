def get_model_fields(model: type[BaseModel]) -> list[ModelField]:
    model_fields: list[ModelField] = []
    for name, field_info in model.model_fields.items():
        type_ = field_info.annotation
        if lenient_issubclass(type_, (BaseModel, dict)) or is_dataclass(type_):
            model_config = None
        else:
            model_config = model.model_config
        model_fields.append(
            ModelField(
                field_info=field_info,
                name=name,
                config=model_config,
            )
        )
    return model_fields