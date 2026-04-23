def update_model_options_in_build_config(
    component: Any,
    build_config: dict,
    cache_key_prefix: str,
    get_options_func,
    field_name: str | None = None,
    field_value: Any = None,
    model_field_name: str = "model",
) -> dict:
    """Helper function to update build config with cached model options."""
    import time

    # Check if component specified static options - if so, preserve them
    # The cache key for static options detection
    static_options_cache_key = f"{cache_key_prefix}_static_options_detected"

    # On initial load, check if the component has static options
    if field_name is None and static_options_cache_key not in component.cache:
        # Check if the model field in build_config already has options set
        existing_options = build_config.get(model_field_name, {}).get("options")
        if existing_options:
            # Component specified static options - mark them as static
            component.cache[static_options_cache_key] = True
        else:
            component.cache[static_options_cache_key] = False

    # If component has static options, skip the refresh logic entirely
    if component.cache.get(static_options_cache_key, False):
        # Static options - don't override them
        # Just handle the visibility logic and return
        if field_value == "connect_other_models":
            # User explicitly selected "Connect other models", show the handle
            if cache_key_prefix == "embedding_model_options":
                build_config[model_field_name]["input_types"] = ["Embeddings"]
            else:
                build_config[model_field_name]["input_types"] = ["LanguageModel"]
        else:
            # Default case or model selection: hide the handle
            build_config[model_field_name]["input_types"] = []
        return build_config

    # Cache key based on user_id
    cache_key = f"{cache_key_prefix}_{component.user_id}"
    cache_timestamp_key = f"{cache_key}_timestamp"
    cache_ttl = _MODEL_OPTIONS_CACHE_TTL_SECONDS

    # Check if cache is expired
    cache_expired = False
    if cache_timestamp_key in component.cache:
        time_since_cache = time.time() - component.cache[cache_timestamp_key]
        cache_expired = time_since_cache > cache_ttl

    # Check if we need to refresh
    should_refresh = (
        field_name == "api_key"  # API key changed
        or field_name is None  # Initial load
        or field_name == model_field_name  # Model field refresh button clicked
        or cache_key not in component.cache  # Cache miss
        or cache_expired  # Cache expired
    )

    if should_refresh:
        # Fetch options based on user's enabled models
        try:
            options = get_options_func(user_id=component.user_id)
            # Cache the results with timestamp
            component.cache[cache_key] = {"options": options}
            component.cache[cache_timestamp_key] = time.time()
        except KeyError as exc:
            # If we can't get user-specific options, fall back to empty.
            # Logged as warning (not debug) so silent UI failures are visible
            # in server logs for easier troubleshooting.
            logger.warning("Failed to fetch user-specific model options: %s", exc)
            component.cache[cache_key] = {"options": []}
            component.cache[cache_timestamp_key] = time.time()

    # Use cached results
    cached = component.cache.get(cache_key, {"options": []})
    build_config[model_field_name]["options"] = cached["options"]

    # Sticky-default: if the currently saved value references a model that
    # isn't in the freshly-fetched options list (e.g. an imported flow whose
    # exporter had providers the importing user hasn't enabled, or a model
    # whose provider was toggled off after saving), inject the saved value
    # into the options list with a ``not_enabled_locally`` metadata flag.
    # The frontend surfaces a "configure" wrench next to the trigger when it
    # sees this flag so the user can enable the provider without silently
    # losing their selection.
    current_value = build_config.get(model_field_name, {}).get("value")
    if (
        isinstance(current_value, list)
        and current_value
        and isinstance(current_value[0], dict)
        and current_value[0].get("name")
    ):
        saved = current_value[0]
        saved_name = saved["name"]
        saved_provider = saved.get("provider", "")
        options_list = build_config[model_field_name]["options"]
        already_present = any(
            opt.get("name") == saved_name and opt.get("provider", "") == saved_provider for opt in options_list
        )
        if not already_present:
            injected = {**saved, "metadata": {**(saved.get("metadata") or {}), "not_enabled_locally": True}}
            build_config[model_field_name]["options"] = [*options_list, injected]

    # Set default value on initial load when the model field has no value.
    # We check the model field's own value (not field_value, which is the value
    # of whatever field triggered the update — e.g. api_key text).  Using
    # field_value here would incorrectly reset the model selection whenever a
    # non-model field (like api_key) is cleared or set to a global variable.
    current_model_value = build_config.get(model_field_name, {}).get("value")
    if not current_model_value:
        options = cached.get("options", [])
        if options:
            # Determine model type based on cache_key_prefix
            model_type = "embeddings" if cache_key_prefix == "embedding_model_options" else "language"

            # Try to get user's default model from the variable service
            default_model_name = None
            default_model_provider = None
            try:

                async def _get_default_model():
                    async with session_scope() as session:
                        variable_service = get_variable_service()
                        if variable_service is None:
                            return None, None
                        from langflow.services.variable.service import (
                            DatabaseVariableService,
                        )

                        if not isinstance(variable_service, DatabaseVariableService):
                            return None, None

                        # Variable names match those in the API
                        var_name = (
                            "__default_embedding_model__"
                            if model_type == "embeddings"
                            else "__default_language_model__"
                        )

                        try:
                            var = await variable_service.get_variable_object(
                                user_id=(
                                    UUID(component.user_id) if isinstance(component.user_id, str) else component.user_id
                                ),
                                name=var_name,
                                session=session,
                            )
                            if var and var.value:
                                parsed_value = json.loads(var.value)
                                if isinstance(parsed_value, dict):
                                    return parsed_value.get("model_name"), parsed_value.get("provider")
                        except (ValueError, json.JSONDecodeError, TypeError):
                            # Variable not found or invalid format
                            logger.info(
                                "Variable not found or invalid format: var_name=%s, user_id=%s, model_type=%s",
                                var_name,
                                component.user_id,
                                model_type,
                                exc_info=True,
                            )
                        return None, None

                default_model_name, default_model_provider = run_until_complete(_get_default_model())
            except Exception:  # noqa: BLE001
                # If we can't get default model, continue without it
                logger.info("Failed to get default model, continue without it", exc_info=True)

            # Find the default model in options
            default_model = None
            if default_model_name and default_model_provider:
                # Look for the user's preferred default model
                for opt in options:
                    if opt.get("name") == default_model_name and opt.get("provider") == default_model_provider:
                        default_model = opt
                        break

            # If user's default not found, fallback to first option
            if not default_model and options:
                default_model = options[0]

            # Set the value
            if default_model:
                build_config[model_field_name]["value"] = [default_model]

    # Handle visibility of the model input handle based on selection
    if cache_key_prefix == "embedding_model_options":
        build_config[model_field_name]["input_types"] = ["Embeddings"]
    else:
        build_config[model_field_name]["input_types"] = ["LanguageModel"]

    return build_config