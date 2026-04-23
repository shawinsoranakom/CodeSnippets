async def read_variables(
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
):
    """Read all variables.

    Model provider credentials are validated when they are created or updated,
    not on every read. This avoids latency from external API calls on read operations.

    Returns a list of variables.
    """
    variable_service = get_variable_service()
    if not isinstance(variable_service, DatabaseVariableService):
        msg = "Variable service is not an instance of DatabaseVariableService"
        raise TypeError(msg)
    try:
        all_variables = await variable_service.get_all(user_id=current_user.id, session=session)

        # Filter out internal variables (those starting and ending with __)
        filtered_variables = [
            var for var in all_variables if not (var.name and var.name.startswith("__") and var.name.endswith("__"))
        ]

        # Mark model provider credentials - validation status is based on existence
        # (actual validation happens on create/update)
        for var in filtered_variables:
            if var.name and var.name in model_provider_variable_mapping.values() and var.type == CREDENTIAL_TYPE:
                # Credential exists and was validated on save
                var.is_valid = True
                var.validation_error = None
            else:
                # Not a model provider credential
                var.is_valid = None
                var.validation_error = None

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    else:
        return filtered_variables