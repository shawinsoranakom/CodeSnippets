async def _get_enabled_models(session: DbSession, current_user: CurrentActiveUser) -> set[str]:
    """Helper function to get the set of explicitly enabled model IDs.

    These are models that were NOT default but were explicitly enabled by the user.
    """
    variable_service = get_variable_service()
    if not isinstance(variable_service, DatabaseVariableService):
        return set()

    try:
        var = await variable_service.get_variable_object(
            user_id=current_user.id, name=ENABLED_MODELS_VAR, session=session
        )
        # Strip whitespace and check if value is non-empty
        if var.value and (value_stripped := var.value.strip()):
            try:
                parsed_value = json.loads(value_stripped)
                # Validate it's a list of strings
                if not isinstance(parsed_value, list):
                    logger.warning("Invalid enabled models format for user %s: not a list", current_user.id)
                    return set()
                # Ensure all items are strings
                return {str(item) for item in parsed_value if isinstance(item, str)}
            except (json.JSONDecodeError, TypeError):
                # Log at debug level to avoid flooding logs with expected edge cases
                logger.debug("Failed to parse enabled models for user %s: %s", current_user.id, var.value)
                return set()
    except ValueError:
        # Variable not found, return empty set
        pass
    return set()