async def _get_model_status(user_id: UUID | str) -> tuple[set[str], set[str]]:
    """Fetch disabled and explicitly enabled model sets for a user.

    Returns:
        A tuple of (disabled_models, explicitly_enabled_models).
    """
    async with session_scope() as session:
        variable_service = get_variable_service()
        if variable_service is None:
            return set(), set()
        from langflow.services.variable.service import DatabaseVariableService

        if not isinstance(variable_service, DatabaseVariableService):
            return set(), set()
        all_vars = await variable_service.get_all(
            user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
            session=session,
        )
        disabled: set[str] = set()
        enabled: set[str] = set()
        for var in all_vars:
            if var.name == "__disabled_models__" and var.value:
                with contextlib.suppress(json.JSONDecodeError, TypeError):
                    disabled = set(json.loads(var.value))
            elif var.name == "__enabled_models__" and var.value:
                with contextlib.suppress(json.JSONDecodeError, TypeError):
                    enabled = set(json.loads(var.value))
        return disabled, enabled