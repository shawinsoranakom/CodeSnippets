def handle_model_input_update(
    component: Any,
    build_config: dict,
    field_value: Any,
    field_name: str | None = None,
    *,
    cache_key_prefix: str = "language_model_options",
    get_options_func=None,
    model_field_name: str = "model",
) -> dict:
    """Full update_build_config lifecycle for any component with a ModelInput."""
    from lfx.base.models import unified_models as unified_models_module

    # If get_options_func is not provided, use the default based on cache_key_prefix
    if get_options_func is None:
        get_options_func = unified_models_module.get_language_model_options

    # Step 1: Refresh/cache model options, set defaults and input_types
    build_config = update_model_options_in_build_config(
        component=component,
        build_config=build_config,
        cache_key_prefix=cache_key_prefix,
        get_options_func=get_options_func,
        field_name=field_name,
        field_value=field_value,
        model_field_name=model_field_name,
    )

    # When the user directly edits a provider-specific field (e.g. api_key),
    # skip the provider reset/re-population so their value is preserved.
    provider_mapped_fields = _get_all_provider_mapped_fields()
    if field_name in provider_mapped_fields:
        return build_config

    # If the model field is in connection mode (user chose "Connect other models"),
    # skip auto-selection and provider re-population so credentials stay cleared.
    if build_config.get(model_field_name, {}).get("_connection_mode"):
        return build_config

    # When the user changes the model selection, we need to reset/hide fields that may no longer apply
    if field_name == model_field_name:
        options = build_config[model_field_name].get("options", [])
        build_config[model_field_name]["options"] = options

        value_missing = not field_value or field_value[0] not in options
        if value_missing:
            # If the current value is not in the options (e.g. user switched to a model that
            # is no longer available), reset to avoid confusion so the user can pick a valid one.
            option_names = {opt["name"] for opt in options}
            value_is_valid = bool(field_value) and field_value[0]["name"] in option_names

            # If the value is invalid, reset to the first option if available, otherwise empty.
            build_config[model_field_name]["value"] = field_value if value_is_valid else [options[0]] if options else ""
            field_value = build_config[model_field_name]["value"]

    # Step 2: Hide all provider-specific fields.  We do NOT clear values
    # here — the frontend has already mutated ``template[model]["value"]``
    # to the new selection before POSTing, so the backend can't distinguish
    # a real provider switch from a same-provider refresh based on the
    # incoming build_config alone.  Instead,
    # ``apply_provider_variable_config_to_build_config`` (Step 3) handles
    # the credential swap by detecting stale cross-provider variable keys
    # in provider-mapped fields and replacing them with the current
    # provider's var key.  Raw user-typed values are preserved in all cases.
    for field in provider_mapped_fields:
        if field in build_config:
            field_config = build_config[field]
            field_config["show"] = False
            field_config["required"] = False

    # Step 3: Show/configure the right fields for the selected provider
    # Use field_value when the user actively changed the model selection;
    # otherwise (initial load with empty field_value, or other field changes)
    # fall back to the value in build_config (which Step 1 may have set to the default model).
    current_model_value = (
        field_value
        if field_name == model_field_name and field_value
        else build_config.get(model_field_name, {}).get("value")
    )
    if isinstance(current_model_value, list) and len(current_model_value) > 0:
        provider = current_model_value[0].get("provider", "")
        if provider:
            build_config = unified_models_module.apply_provider_variable_config_to_build_config(build_config, provider)

            # Resolve DropdownInput field values from the provider's configured
            # variables.  load_from_db doesn't work for dropdowns because the
            # variable key name isn't a valid dropdown option.
            if hasattr(component, "user_id") and component.user_id:
                _resolve_dropdown_provider_values(component.user_id, build_config, provider)

        # Also handle WatsonX-specific embedding fields that are not in provider metadata
        if cache_key_prefix == "embedding_model_options":
            is_watsonx = provider == "IBM WatsonX"
            if "truncate_input_tokens" in build_config:
                build_config["truncate_input_tokens"]["show"] = is_watsonx
            if "input_text" in build_config:
                build_config["input_text"]["show"] = is_watsonx

    # Ensure the API key field is always visible regardless of provider selection
    if "api_key" in build_config:
        build_config["api_key"]["show"] = True

    return build_config