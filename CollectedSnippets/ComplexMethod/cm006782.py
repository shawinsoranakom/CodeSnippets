async def _get_all_variables():
        async with session_scope() as session:
            variable_service = get_variable_service()
            if variable_service is None:
                return {}

            values = {}
            user_id_uuid = UUID(user_id) if isinstance(user_id, str) else user_id

            for var_info in provider_vars:
                var_key = var_info.get("variable_key")
                if not var_key:
                    continue

                try:
                    value = await variable_service.get_variable(
                        user_id=user_id_uuid,
                        name=var_key,
                        field="",
                        session=session,
                    )
                    if value and str(value).strip():
                        values[var_key] = str(value)
                except (ValueError, Exception):  # noqa: BLE001
                    # Variable not found - check environment
                    env_value = os.environ.get(var_key)
                    if env_value and env_value.strip():
                        values[var_key] = env_value

            return values