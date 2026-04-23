async def update_variable(
    *,
    session: DbSession,
    variable_id: UUID,
    variable: VariableUpdate,
    current_user: CurrentActiveUser,
):
    """Update a variable."""
    variable_service = get_variable_service()
    if not isinstance(variable_service, DatabaseVariableService):
        msg = "Variable service is not an instance of DatabaseVariableService"
        raise TypeError(msg)
    try:
        # Get existing variable to check if it's a model provider credential
        existing_variable = await variable_service.get_variable_by_id(
            user_id=current_user.id, variable_id=variable_id, session=session
        )

        # Validate API key if updating a model provider variable
        if existing_variable.name in model_provider_variable_mapping.values() and variable.value:
            provider = get_provider_from_variable_name(existing_variable.name)
            if provider is not None:
                # Run validation off the event loop to avoid blocking
                try:
                    await asyncio.to_thread(
                        validate_model_provider_key,
                        provider,
                        {existing_variable.name: variable.value},
                    )
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=str(e)) from e

        return await variable_service.update_variable_fields(
            user_id=current_user.id,
            variable_id=variable_id,
            variable=variable,
            session=session,
        )
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail="Variable not found") from e
    except ValueError as e:
        raise HTTPException(status_code=404, detail="Variable not found") from e
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e)) from e