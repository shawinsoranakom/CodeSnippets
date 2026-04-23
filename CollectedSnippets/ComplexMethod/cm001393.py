def _recursive_init_model(
    model: Type[M],
    infer_field_value: Callable[[FieldInfo], Any],
) -> M:
    """
    Recursively initialize the user configuration fields of a Pydantic model.

    Parameters:
        model: The Pydantic model type.
        infer_field_value: A callback function to infer the value of each field.
            Parameters:
                ModelField: The Pydantic ModelField object describing the field.

    Returns:
        BaseModel: An instance of the model with the initialized configuration.
    """
    user_config_fields = {}
    for name, field in model.model_fields.items():
        if _get_field_metadata(field, "user_configurable"):
            user_config_fields[name] = infer_field_value(field)
        elif isinstance(field.annotation, ModelMetaclass) and issubclass(
            field.annotation, SystemConfiguration
        ):
            try:
                user_config_fields[name] = _recursive_init_model(
                    model=field.annotation,
                    infer_field_value=infer_field_value,
                )
            except ValidationError as e:
                # Gracefully handle missing fields
                if all(e["type"] == "missing" for e in e.errors()):
                    user_config_fields[name] = None
                raise

    user_config_fields = remove_none_items(user_config_fields)

    return model.model_validate(user_config_fields)