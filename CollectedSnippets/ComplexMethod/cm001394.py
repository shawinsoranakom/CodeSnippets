def _recurse_user_config_fields(
    model: BaseModel,
    infer_field_value: Callable[[FieldInfo, Any], Any],
    init_sub_config: Optional[
        Callable[[Type[SystemConfiguration]], SystemConfiguration | None]
    ] = None,
) -> dict[str, Any]:
    """
    Recursively process the user configuration fields of a Pydantic model instance.

    Params:
        model: The Pydantic model to iterate over.
        infer_field_value: A callback function to process each field.
            Params:
                ModelField: The Pydantic ModelField object describing the field.
                Any: The current value of the field.
        init_sub_config: An optional callback function to initialize a sub-config.
            Params:
                Type[SystemConfiguration]: The type of the sub-config to initialize.

    Returns:
        dict[str, Any]: The processed user configuration fields of the instance.
    """
    user_config_fields = {}

    for name, field in model.model_fields.items():
        value = getattr(model, name)

        # Handle individual field
        if _get_field_metadata(field, "user_configurable"):
            user_config_fields[name] = infer_field_value(field, value)

        # Recurse into nested config object
        elif isinstance(value, SystemConfiguration):
            user_config_fields[name] = _recurse_user_config_fields(
                model=value,
                infer_field_value=infer_field_value,
                init_sub_config=init_sub_config,
            )

        # Recurse into optional nested config object
        elif value is None and init_sub_config:
            field_type = get_args(field.annotation)[0]  # Optional[T] -> T
            if type(field_type) is ModelMetaclass and issubclass(
                field_type, SystemConfiguration
            ):
                sub_config = init_sub_config(field_type)
                if sub_config:
                    user_config_fields[name] = _recurse_user_config_fields(
                        model=sub_config,
                        infer_field_value=infer_field_value,
                        init_sub_config=init_sub_config,
                    )

        elif isinstance(value, list) and all(
            isinstance(i, SystemConfiguration) for i in value
        ):
            user_config_fields[name] = [
                _recurse_user_config_fields(i, infer_field_value, init_sub_config)
                for i in value
            ]
        elif isinstance(value, dict) and all(
            isinstance(i, SystemConfiguration) for i in value.values()
        ):
            user_config_fields[name] = {
                k: _recurse_user_config_fields(v, infer_field_value, init_sub_config)
                for k, v in value.items()
            }

    return user_config_fields