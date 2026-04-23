def _validate_and_get_enabled_providers(
    all_variables: dict[str, Any],
    provider_variable_map: dict[str, str],
    *,
    skip_validation: bool = True,
) -> set[str]:
    """Return set of enabled providers based on credential existence."""
    from langflow.services.auth import utils as auth_utils
    from langflow.services.deps import get_settings_service

    settings_service = get_settings_service()
    enabled = set()

    for provider in provider_variable_map:
        provider_vars = get_provider_all_variables(provider)

        collected_values: dict[str, str] = {}
        all_required_present = True

        for var_info in provider_vars:
            var_key = var_info.get("variable_key")
            if not var_key:
                continue

            is_required = bool(var_info.get("required", False))
            value = None

            if var_key in all_variables:
                variable = all_variables[var_key]
                if variable.value is not None:
                    try:
                        decrypted_value = auth_utils.decrypt_api_key(variable.value, settings_service=settings_service)
                        if decrypted_value and decrypted_value.strip():
                            value = decrypted_value
                    except Exception as e:  # noqa: BLE001
                        raw_value = variable.value
                        if raw_value is not None and str(raw_value).strip():
                            value = str(raw_value)
                        else:
                            logger.debug(
                                "Failed to decrypt variable %s for provider %s: %s",
                                var_key,
                                provider,
                                e,
                            )

            if value is None:
                env_value = os.environ.get(var_key)
                if env_value and env_value.strip() and env_value.strip() != "dummy":
                    value = env_value
                    logger.debug(
                        "Using environment variable %s for provider %s",
                        var_key,
                        provider,
                    )

            if value:
                collected_values[var_key] = value
            elif is_required:
                all_required_present = False

        if not provider_vars:
            enabled.add(provider)
        elif all_required_present and collected_values:
            if skip_validation:
                # Just check existence - validation was done on save
                enabled.add(provider)
            else:
                try:
                    validate_model_provider_key(provider, collected_values)
                    enabled.add(provider)
                except (ValueError, Exception) as e:  # noqa: BLE001
                    logger.debug("Provider %s validation failed: %s", provider, e)

    return enabled