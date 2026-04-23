def _resolve_var_name(var_name: str) -> str | None:
        env_value = os.environ.get(var_name)
        if env_value and env_value.strip():
            return env_value.strip()
        if user_id and not (isinstance(user_id, str) and user_id == "None"):

            async def _get_by_var_name():
                async with session_scope() as session:
                    variable_service = get_variable_service()
                    if variable_service is None:
                        return None
                    try:
                        return await variable_service.get_variable(
                            user_id=(UUID(user_id) if isinstance(user_id, str) else user_id),
                            name=var_name,
                            field="",
                            session=session,
                        )
                    except ValueError:
                        return None

            value = run_until_complete(_get_by_var_name())
            if value and str(value).strip():
                return str(value).strip()
        return None