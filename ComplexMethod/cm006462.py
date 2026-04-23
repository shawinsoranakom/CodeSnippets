async def _cleanup_model_list_variable(
    variable_service: DatabaseVariableService,
    user_id: UUID,
    variable_name: str,
    models_to_remove: set[str],
    session: DbSession,
) -> None:
    """Remove specified models from a model list variable (disabled or enabled models).

    If all models are removed, the variable is deleted entirely.
    If the variable doesn't exist, this is a no-op.
    """
    try:
        model_list_var = await variable_service.get_variable_object(
            user_id=user_id, name=variable_name, session=session
        )
    except ValueError:
        # Variable doesn't exist, nothing to clean up
        return

    if not model_list_var or not model_list_var.value:
        return

    # Parse current models
    try:
        current_models = set(json.loads(model_list_var.value))
    except (json.JSONDecodeError, TypeError):
        current_models = set()

    # Filter out the provider's models
    filtered_models = current_models - models_to_remove

    # Nothing changed, no update needed
    if filtered_models == current_models:
        return

    if filtered_models:
        # Update with filtered list
        if model_list_var.id is not None:
            await variable_service.update_variable_fields(
                user_id=user_id,
                variable_id=model_list_var.id,
                variable=VariableUpdate(
                    id=model_list_var.id,
                    name=variable_name,
                    value=json.dumps(list(filtered_models)),
                    type=GENERIC_TYPE,
                ),
                session=session,
            )
    else:
        # No models left, delete the variable
        await variable_service.delete_variable(user_id=user_id, name=variable_name, session=session)