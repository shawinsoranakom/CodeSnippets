async def get_enabled_providers(
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
    providers: Annotated[list[str] | None, Query()] = None,
):
    """Get enabled providers for the current user.

    Providers are considered enabled if they have a credential variable stored.
    API key validation is performed when credentials are saved, not on every read,
    to avoid latency from external API calls.
    """
    variable_service = get_variable_service()
    try:
        if not isinstance(variable_service, DatabaseVariableService):
            raise HTTPException(
                status_code=500,
                detail="Variable service is not an instance of DatabaseVariableService",
            )
        # Get all variables (VariableRead objects)
        all_variables = await variable_service.get_all(user_id=current_user.id, session=session)

        # Build a set of all variable names we have
        all_variable_names = {var.name for var in all_variables}

        # Get the provider-variable mapping
        provider_variable_map = get_model_provider_variable_mapping()

        # Check which providers have all required variables saved
        enabled_providers = []
        provider_status = {}

        for provider in provider_variable_map:
            # Get ALL variables for this provider
            provider_vars = get_provider_all_variables(provider)

            # Check if all REQUIRED variables are present
            required_vars = [v for v in provider_vars if v.get("required", False)]
            all_required_present = all(v.get("variable_key") in all_variable_names for v in required_vars)

            provider_status[provider] = all_required_present
            if all_required_present:
                enabled_providers.append(provider)

        result = {
            "enabled_providers": enabled_providers,
            "provider_status": provider_status,
        }

        if providers:
            # Filter enabled_providers and provider_status by requested providers
            filtered_enabled = [p for p in result["enabled_providers"] if p in providers]
            provider_status_dict = result.get("provider_status", {})
            if not isinstance(provider_status_dict, dict):
                provider_status_dict = {}
            filtered_status = {p: v for p, v in provider_status_dict.items() if p in providers}
            return {
                "enabled_providers": filtered_enabled,
                "provider_status": filtered_status,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get enabled providers for user %s", current_user.id)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve enabled providers. Please try again later.",
        ) from e
    else:
        return result