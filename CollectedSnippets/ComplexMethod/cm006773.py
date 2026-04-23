def _resolve_dropdown_provider_values(
    user_id,
    build_config: dict,
    provider: str,
) -> None:
    """Resolve actual values for DropdownInput fields from provider variables.

    DropdownInput fields cannot use the load_from_db mechanism because the
    variable key name (e.g. ``WATSONX_URL``) is not a valid dropdown option.
    Instead, we resolve the stored value from the database/environment and
    set it directly on the field.
    """
    from lfx.base.models import unified_models as unified_models_module

    provider_vars = unified_models_module.get_provider_all_variables(provider)

    # Collect dropdown fields that need resolution
    dropdown_var_keys: dict[str, str] = {}  # var_key -> mapping_field
    for var_info in provider_vars:
        component_meta = var_info.get("component_metadata", {})
        mapping_field = component_meta.get("mapping_field")
        if not mapping_field or mapping_field not in build_config:
            continue

        field_config = build_config[mapping_field]
        if field_config.get("_input_type") != "DropdownInput":
            continue

        var_key = var_info.get("variable_key")
        if var_key:
            dropdown_var_keys[var_key] = mapping_field

    if not dropdown_var_keys:
        return

    # Resolve all provider variables at once
    all_vars = unified_models_module.get_all_variables_for_provider(user_id, provider)

    for var_key, field_name in dropdown_var_keys.items():
        field_config = build_config[field_name]
        resolved_value = all_vars.get(var_key)
        if resolved_value:
            field_config["value"] = resolved_value
            field_config["load_from_db"] = False
            logger.debug(
                "Resolved DropdownInput field %s to %s",
                field_name,
                resolved_value,
            )
        else:
            # If we can't resolve, fall back to the first dropdown option
            options = field_config.get("options", [])
            if options:
                field_config["value"] = options[0]
            field_config["load_from_db"] = False
            logger.debug(
                "Could not resolve variable %s for DropdownInput field %s, using default",
                var_key,
                field_name,
            )