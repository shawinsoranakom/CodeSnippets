async def get_default_model(
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
    model_type: Annotated[str, Query(description="Type of model: 'language' or 'embedding'")] = "language",
):
    """Get the default model for the current user."""
    variable_service = get_variable_service()
    if not isinstance(variable_service, DatabaseVariableService):
        return {"default_model": None}

    var_name = DEFAULT_LANGUAGE_MODEL_VAR if model_type == "language" else DEFAULT_EMBEDDING_MODEL_VAR

    try:
        var = await variable_service.get_variable_object(user_id=current_user.id, name=var_name, session=session)
        if var.value:
            try:
                parsed_value = json.loads(var.value)
            except (json.JSONDecodeError, TypeError):
                logger.warning("Failed to parse default model for user %s", current_user.id, exc_info=True)
                return {"default_model": None}
            else:
                # Validate structure
                if not isinstance(parsed_value, dict) or not all(
                    k in parsed_value for k in ("model_name", "provider", "model_type")
                ):
                    logger.warning("Invalid default model format for user %s", current_user.id)
                    return {"default_model": None}
                return {"default_model": parsed_value}
    except ValueError:
        # Variable not found
        pass
    return {"default_model": None}