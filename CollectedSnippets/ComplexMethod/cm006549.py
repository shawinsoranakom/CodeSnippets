async def update_params_with_load_from_db_fields(
    custom_component: Component,
    params,
    load_from_db_fields,
    *,
    fallback_to_env_vars=False,
):
    async with session_scope() as session:
        for field in load_from_db_fields:
            if field not in params or not params[field]:
                continue

            try:
                key = await custom_component.get_variable(name=params[field], field=field, session=session)
            except ValueError as e:
                if "User id is not set" in str(e):
                    raise
                if "variable not found." in str(e) and not fallback_to_env_vars:
                    raise
                await logger.adebug(str(e))
                key = None

            if fallback_to_env_vars and key is None:
                key = os.getenv(params[field])
                if key:
                    await logger.ainfo(f"Using environment variable {params[field]} for {field}")
                else:
                    await logger.aerror(f"Environment variable {params[field]} is not set.")

            params[field] = key if key is not None else None
            if key is None:
                await logger.awarning(f"Could not get value for {field}. Setting it to None.")

        return params