async def create_variable(
    *,
    session: DbSession,
    variable: VariableCreate,
    current_user: CurrentActiveUser,
):
    """Create a new variable."""
    variable_service = get_variable_service()
    if not variable.name and not variable.value:
        raise HTTPException(status_code=400, detail="Variable name and value cannot be empty")

    if not variable.name:
        raise HTTPException(status_code=400, detail="Variable name cannot be empty")

    if not variable.value:
        raise HTTPException(status_code=400, detail="Variable value cannot be empty")

    if variable.name in await variable_service.list_variables(user_id=current_user.id, session=session):
        raise HTTPException(status_code=400, detail="Variable name already exists")

    # Check if the variable is a reserved model provider variable
    if variable.name in model_provider_variable_mapping.values():
        provider = get_provider_from_variable_name(variable.name)
        if provider is not None:
            # Validate that the key actually works using the Language Model Service
            # Run validation off the event loop to avoid blocking
            try:
                await asyncio.to_thread(validate_model_provider_key, provider, {variable.name: variable.value})
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e)) from e

    try:
        return await variable_service.create_variable(
            user_id=current_user.id,
            name=variable.name,
            value=variable.value,
            default_fields=variable.default_fields or [],
            type_=variable.type or CREDENTIAL_TYPE,
            session=session,
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e)) from e