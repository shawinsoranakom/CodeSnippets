def set_attr_from_env(sub_config: BaseModel, prefix: str = '') -> None:
        """Set attributes of a config model based on environment variables."""
        for field_name, field_info in sub_config.__class__.model_fields.items():
            field_value = getattr(sub_config, field_name)
            field_type = field_info.annotation

            # compute the expected env var name from the prefix and field name
            # e.g. LLM_BASE_URL
            env_var_name = (prefix + field_name).upper()

            cast_value: Any
            if isinstance(field_value, BaseModel):
                set_attr_from_env(field_value, prefix=field_name + '_')

            elif env_var_name in env_or_toml_dict:
                # convert the env var to the correct type and set it
                value = env_or_toml_dict[env_var_name]

                # skip empty config values (fall back to default)
                if not value:
                    continue

                try:
                    # if it's an optional type, get the non-None type
                    if get_origin(field_type) is UnionType:
                        field_type = get_optional_type(field_type)

                    # Attempt to cast the env var to type hinted in the dataclass
                    if field_type is bool:
                        cast_value = str(value).lower() in ['true', '1']
                    # parse dicts and lists like SANDBOX_RUNTIME_STARTUP_ENV_VARS and SANDBOX_RUNTIME_EXTRA_BUILD_ARGS
                    elif (
                        get_origin(field_type) is dict
                        or get_origin(field_type) is list
                        or field_type is dict
                        or field_type is list
                    ):
                        cast_value = literal_eval(value)
                        # If it's a list of Pydantic models
                        if get_origin(field_type) is list:
                            inner_type = get_args(field_type)[0]
                            if isinstance(inner_type, type) and issubclass(
                                inner_type, BaseModel
                            ):
                                cast_value = [
                                    inner_type(**item)
                                    if isinstance(item, dict)
                                    else item
                                    for item in cast_value
                                ]
                    else:
                        if field_type is not None:
                            cast_value = field_type(value)
                    setattr(sub_config, field_name, cast_value)
                except (ValueError, TypeError):
                    logger.openhands_logger.error(
                        f'Error setting env var {env_var_name}={value}: check that the value is of the right type'
                    )