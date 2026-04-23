async def set_default_model(
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
    request: DefaultModelRequest,
):
    """Set the default model for the current user."""
    variable_service = get_variable_service()
    if not isinstance(variable_service, DatabaseVariableService):
        raise HTTPException(
            status_code=500,
            detail="Variable service is not an instance of DatabaseVariableService",
        )

    var_name = DEFAULT_LANGUAGE_MODEL_VAR if request.model_type == "language" else DEFAULT_EMBEDDING_MODEL_VAR

    # Log the operation for audit trail
    logger.info(
        "User %s setting default %s model to %s (%s)",
        current_user.id,
        request.model_type,
        request.model_name,
        request.provider,
    )

    # Prepare the model data
    model_data = {
        "model_name": request.model_name,
        "provider": request.provider,
        "model_type": request.model_type,
    }
    model_json = json.dumps(model_data)

    # Check if the variable already exists
    try:
        existing_var = await variable_service.get_variable_object(
            user_id=current_user.id, name=var_name, session=session
        )
        if existing_var is None or existing_var.id is None:
            msg = f"Variable {DISABLED_MODELS_VAR} not found"
            raise ValueError(msg)
        # Update existing variable
        from langflow.services.database.models.variable.model import VariableUpdate

        await variable_service.update_variable_fields(
            user_id=current_user.id,
            variable_id=existing_var.id,
            variable=VariableUpdate(id=existing_var.id, name=var_name, value=model_json, type=GENERIC_TYPE),
            session=session,
        )
    except ValueError:
        # Variable not found, create new one
        await variable_service.create_variable(
            user_id=current_user.id,
            name=var_name,
            value=model_json,
            type_=GENERIC_TYPE,
            session=session,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Failed to set default model for user %s",
            current_user.id,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to set default model. Please try again later.",
        ) from e

    return {"default_model": model_data}