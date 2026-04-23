async def _get_disabled_models(session: DbSession, current_user: CurrentActiveUser) -> set[str]:
    """Helper function to get the set of disabled model IDs."""
    variable_service = get_variable_service()
    if not isinstance(variable_service, DatabaseVariableService):
        return set()

    try:
        var = await variable_service.get_variable_object(
            user_id=current_user.id, name=DISABLED_MODELS_VAR, session=session
        )
        if var.value:  # This checks for both None and empty string
            try:
                parsed_value = json.loads(var.value)
                # Validate it's a list of strings
                if not isinstance(parsed_value, list):
                    logger.warning("Invalid disabled models format for user %s: not a list", current_user.id)
                    return set()
                # Ensure all items are strings
                return {str(item) for item in parsed_value if isinstance(item, str)}
            except (json.JSONDecodeError, TypeError):
                logger.warning("Failed to parse disabled models for user %s", current_user.id, exc_info=True)
                return set()
    except ValueError:
        # Variable not found, return empty set
        pass
    return set()