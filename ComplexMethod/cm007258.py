async def update_params_with_load_from_db_fields(
    custom_component: CustomComponent,
    params,
    load_from_db_fields,
    *,
    fallback_to_env_vars=False,
):
    async with session_scope() as session:
        settings_service = get_settings_service()
        is_noop_session = isinstance(session, NoopSession) or (
            settings_service and settings_service.settings.use_noop_database
        )
        if is_noop_session:
            logger.debug("Loading variables from environment variables because database is not available.")
            context = None
            if hasattr(custom_component, "graph") and hasattr(custom_component.graph, "context"):
                context = custom_component.graph.context
            return load_from_env_vars(params, load_from_db_fields, context=context)
        for field in load_from_db_fields:
            # Check if this is a table field (using our naming convention)
            if field.startswith("table:"):
                table_field_name = field[6:]  # Remove "table:" prefix
                params = await update_table_params_with_load_from_db_fields(
                    custom_component,
                    params,
                    table_field_name,
                    fallback_to_env_vars=fallback_to_env_vars,
                )
            else:
                # Handle regular field-level load_from_db
                if field not in params or not params[field]:
                    continue

                try:
                    key = await custom_component.get_variable(name=params[field], field=field, session=session)
                except ValueError as e:
                    if "User id is not set" in str(e):
                        raise
                    if "variable not found." in str(e) and not fallback_to_env_vars:
                        raise
                    logger.debug(str(e))
                    key = None

                if fallback_to_env_vars and key is None:
                    key = os.getenv(params[field])
                    if key:
                        logger.info(f"Using environment variable {params[field]} for {field}")
                    else:
                        logger.error(f"Environment variable {params[field]} is not set.")

                params[field] = key if key is not None else None
                if key is None:
                    logger.warning(f"Could not get value for {field}. Setting it to None.")

        return params