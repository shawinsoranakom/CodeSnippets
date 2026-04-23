def apply_provider_variable_config_to_build_config(
    build_config: dict,
    provider: str,
) -> dict:
    """Apply provider variable metadata to component build config fields."""
    # Resolve helpers via package namespace so tests patching
    # lfx.base.models.unified_models.<name> keep working.
    from lfx.base.models import unified_models as unified_models_module

    provider_vars = unified_models_module.get_provider_all_variables(provider)

    """
    First hides all provider-specific fields (so switching e.g. IBM -> OpenAI
    does not leave IBM fields visible), then shows and configures only the
    current provider's fields.
    """
    all_provider_fields = _get_all_provider_specific_field_names()
    for field_name in all_provider_fields:
        if field_name in build_config:
            build_config[field_name]["show"] = False
            build_config[field_name]["required"] = False

    vars_by_field = {}
    for v in provider_vars:
        component_meta = v.get("component_metadata", {})
        mapping_field = component_meta.get("mapping_field")
        if mapping_field:
            vars_by_field[mapping_field] = v

    # Apply the current provider's variable metadata to show/configure the right fields and pre-populate credentials.
    for field_name, var_info in vars_by_field.items():
        if field_name not in build_config:
            continue

        field_config = build_config[field_name]
        component_meta = var_info.get("component_metadata", {})

        # Apply required from component_metadata
        required = component_meta.get("required", False)
        field_config["required"] = required

        # Apply advanced from component_metadata
        advanced = component_meta.get("advanced", False)
        field_config["advanced"] = advanced

        # Apply info from component_metadata
        info = component_meta.get("info")
        if info:
            field_config["info"] = info

        field_config["show"] = True

        # Pre-populate with the variable name (never the raw secret) when a
        # credential is available in the database or environment.  Setting
        # load_from_db=True tells the runtime to resolve the actual value.
        var_key = var_info.get("variable_key")
        if var_key:
            # DropdownInput fields don't support load_from_db because the
            # variable key name (e.g. "WATSONX_URL") isn't a valid dropdown
            # option.  These fields are resolved separately by
            # _resolve_dropdown_provider_values in handle_model_input_update.
            input_type = field_config.get("_input_type", "")
            if input_type == "DropdownInput":
                logger.debug(
                    "Skipping load_from_db for DropdownInput field %s (will resolve separately)",
                    field_name,
                )
            else:
                # Decide whether to install this provider's variable key on
                # the field.  Cases:
                #
                # 1. Empty field — auto-populate.
                # 2. ``load_from_db=True`` with a value that doesn't match
                #    this provider's ``var_key`` — stale cross-provider
                #    credential (e.g. ``ANTHROPIC_API_KEY`` left over after
                #    switching to OpenAI).  Replace with the current
                #    provider's var_key.
                # 3. ``load_from_db=True`` with a value that matches
                #    ``var_key`` — already correct, preserve.
                # 4. ``load_from_db=False`` with a value — user-typed raw
                #    credential.  Preserve so it survives refresh cycles.
                #    We cannot tell from the backend whether a raw value is
                #    stale after a provider switch, so we err on the side
                #    of preservation; the user can overwrite it manually.
                current_value = field_config.get("value")
                current_load_from_db = field_config.get("load_from_db", False)
                is_empty = not current_value
                is_stale_cross_provider_var = current_load_from_db and current_value != var_key
                if is_empty or is_stale_cross_provider_var:
                    field_config["value"] = var_key
                    field_config["load_from_db"] = True
                    logger.debug(
                        "Set field %s to var name %s (value resolved at runtime)",
                        field_name,
                        var_key,
                    )
                else:
                    logger.debug(
                        "Skipping auto-set for field %s - user has already supplied a value",
                        field_name,
                    )

    return build_config