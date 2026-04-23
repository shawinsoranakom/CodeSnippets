def extract_configurable_fields(
    model_class: Type[BaseModel],
) -> list[SettingInfo]:
    """Extract all UserConfigurable fields from a Pydantic model.

    Args:
        model_class: A Pydantic BaseModel class

    Returns:
        List of SettingInfo objects for each configurable field
    """
    settings: list[SettingInfo] = []

    for name, field_info in model_class.model_fields.items():
        # Check if this field is user configurable
        if not _get_field_metadata(field_info, "user_configurable"):
            continue

        # Get the environment variable name
        from_env = _get_field_metadata(field_info, "from_env")
        if from_env is None:
            continue

        # Handle callable from_env (skip these - they're complex)
        if callable(from_env):
            continue

        env_var = from_env
        field_type, choices = _extract_field_type(field_info)

        # Get default value
        default = field_info.default
        if default is not None and hasattr(default, "__class__"):
            # Handle PydanticUndefined
            if "PydanticUndefined" in str(type(default)):
                default = None

        settings.append(
            SettingInfo(
                name=name,
                env_var=env_var,
                description=field_info.description or "",
                field_type=field_type,
                choices=choices,
                default=default,
                required=field_info.is_required(),
            )
        )

    return settings