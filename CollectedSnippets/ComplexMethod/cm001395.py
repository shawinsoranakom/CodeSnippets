def _recurse_user_config_values(
    instance: BaseModel,
    get_field_value: Callable[[FieldInfo, T], T] = lambda _, v: v,
) -> dict[str, Any]:
    """
    This function recursively traverses the user configuration values in a Pydantic
    model instance.

    Params:
        instance: A Pydantic model instance.
        get_field_value: A callback function to process each field. Parameters:
            ModelField: The Pydantic ModelField object that describes the field.
            Any: The current value of the field.

    Returns:
        A dictionary containing the processed user configuration fields of the instance.
    """
    user_config_values = {}

    for name, value in instance.__dict__.items():
        field = instance.model_fields[name]
        if _get_field_metadata(field, "user_configurable"):
            user_config_values[name] = get_field_value(field, value)
        elif isinstance(value, SystemConfiguration):
            user_config_values[name] = _recurse_user_config_values(
                instance=value, get_field_value=get_field_value
            )
        elif isinstance(value, list) and all(
            isinstance(i, SystemConfiguration) for i in value
        ):
            user_config_values[name] = [
                _recurse_user_config_values(i, get_field_value) for i in value
            ]
        elif isinstance(value, dict) and all(
            isinstance(i, SystemConfiguration) for i in value.values()
        ):
            user_config_values[name] = {
                k: _recurse_user_config_values(v, get_field_value)
                for k, v in value.items()
            }

    return user_config_values