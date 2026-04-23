async def _save_model_list_variable(
    variable_service: DatabaseVariableService,
    session: DbSession,
    current_user: CurrentActiveUser,
    var_name: str,
    model_set: set[str],
) -> None:
    """Save or update a model list variable.

    Args:
        variable_service: The database variable service
        session: Database session
        current_user: Current active user
        var_name: Name of the variable to save
        model_set: Set of model names to save

    Raises:
        HTTPException: If there's an error saving the variable
    """
    from langflow.services.database.models.variable.model import VariableUpdate

    models_json = json.dumps(list(model_set))

    try:
        existing_var = await variable_service.get_variable_object(
            user_id=current_user.id, name=var_name, session=session
        )
        if existing_var is None or existing_var.id is None:
            msg = f"Variable {var_name} not found"
            raise ValueError(msg)

        # Update or delete based on whether there are models
        if model_set or var_name == DISABLED_MODELS_VAR:
            # Always update disabled models, even if empty
            # Only update enabled models if non-empty
            await variable_service.update_variable_fields(
                user_id=current_user.id,
                variable_id=existing_var.id,
                variable=VariableUpdate(id=existing_var.id, name=var_name, value=models_json, type=GENERIC_TYPE),
                session=session,
            )
        else:
            # No explicitly enabled models, delete the variable
            await variable_service.delete_variable(user_id=current_user.id, name=var_name, session=session)
    except ValueError:
        # Variable not found, create new one if there are models
        if model_set:
            await variable_service.create_variable(
                user_id=current_user.id,
                name=var_name,
                value=models_json,
                type_=GENERIC_TYPE,
                session=session,
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Failed to save model list variable %s for user %s",
            var_name,
            current_user.id,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to save model configuration. Please try again later.",
        ) from e