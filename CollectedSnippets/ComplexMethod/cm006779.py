async def _fetch_enabled_providers_for_user(user_id: UUID | str) -> set[str]:
    """Shared helper for get_language_model_options and get_embedding_model_options."""
    async with session_scope() as session:
        variable_service = get_variable_service()
        if variable_service is None:
            return set()

        from langflow.services.variable.service import DatabaseVariableService

        if not isinstance(variable_service, DatabaseVariableService):
            return set()

        # Get all variable names (VariableRead has value=None for credentials)
        all_vars = await variable_service.get_all(
            user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
            session=session,
        )
        all_var_names = {var.name for var in all_vars}

        provider_variable_map = get_model_provider_variable_mapping()

        # Build dict with raw Variable values (encrypted for secrets, plaintext for others)
        # We need to fetch raw Variable objects because VariableRead has value=None for credentials
        all_provider_variables = {}
        user_id_uuid = UUID(user_id) if isinstance(user_id, str) else user_id

        for provider in provider_variable_map:
            # Get ALL variables for this provider (not just the primary one)
            provider_vars = get_provider_all_variables(provider)

            for var_info in provider_vars:
                var_name = var_info.get("variable_key")
                if not var_name or var_name not in all_var_names:
                    # Variable not configured by user
                    continue

                if var_name in all_provider_variables:
                    # Already fetched
                    continue

                try:
                    # Get the raw Variable object to access the actual value
                    variable_obj = await variable_service.get_variable_object(
                        user_id=user_id_uuid, name=var_name, session=session
                    )
                    if variable_obj and variable_obj.value:
                        all_provider_variables[var_name] = _VarWithValue(variable_obj.value)
                except Exception as e:  # noqa: BLE001
                    # Variable not found or error accessing it - skip
                    logger.error(f"Error accessing variable {var_name} for provider {provider}: {e}")
                    continue

        # Use shared helper to validate and get enabled providers
        return _validate_and_get_enabled_providers(all_provider_variables, provider_variable_map)