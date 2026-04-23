def add_extra_fields(frontend_node, field_config, function_args) -> None:
    """Add extra fields to the frontend node."""
    if not function_args:
        return
    field_config_ = field_config.copy()
    function_args_names = [arg["name"] for arg in function_args]
    # If kwargs is in the function_args and not all field_config keys are in function_args
    # then we need to add the extra fields

    for extra_field in function_args:
        if "name" not in extra_field or extra_field["name"] in {
            "self",
            "kwargs",
            "args",
        }:
            continue

        field_name, field_type, field_value, field_required = get_field_properties(extra_field)
        config = field_config_.pop(field_name, {})
        frontend_node = add_new_custom_field(
            frontend_node=frontend_node,
            field_name=field_name,
            field_type=field_type,
            field_value=field_value,
            field_required=field_required,
            field_config=config,
        )
    if "kwargs" in function_args_names and not all(key in function_args_names for key in field_config):
        for field_name, config in field_config_.items():
            if "name" not in config or field_name == "code":
                continue
            config_ = config.model_dump() if isinstance(config, BaseModel) else config
            field_name_, field_type, field_value, field_required = get_field_properties(extra_field=config_)
            frontend_node = add_new_custom_field(
                frontend_node=frontend_node,
                field_name=field_name_,
                field_type=field_type,
                field_value=field_value,
                field_required=field_required,
                field_config=config_,
            )