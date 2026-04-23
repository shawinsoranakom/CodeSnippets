async def update_table_params_with_load_from_db_fields(
    custom_component: CustomComponent,
    params: dict,
    table_field_name: str,
    *,
    fallback_to_env_vars: bool = False,
) -> dict:
    """Update table parameters with load_from_db column values."""
    # Get the table data and column metadata
    table_data = params.get(table_field_name, [])
    metadata_key = f"{table_field_name}_load_from_db_columns"
    load_from_db_columns = params.pop(metadata_key, [])

    if not table_data or not load_from_db_columns:
        return params

    # Extract context once for use throughout the function
    context = None
    if hasattr(custom_component, "graph") and hasattr(custom_component.graph, "context"):
        context = custom_component.graph.context

    async with session_scope() as session:
        settings_service = get_settings_service()
        is_noop_session = isinstance(session, NoopSession) or (
            settings_service and settings_service.settings.use_noop_database
        )

        # Process each row in the table
        updated_table_data = []
        for row in table_data:
            if not isinstance(row, dict):
                updated_table_data.append(row)
                continue

            updated_row = row.copy()

            # Process each column that needs database loading
            for column_name in load_from_db_columns:
                if column_name not in updated_row:
                    continue

                # The column value should be the name of the global variable to lookup
                variable_name = updated_row[column_name]
                if not variable_name:
                    continue

                try:
                    if is_noop_session:
                        # Fallback to environment variables
                        key = None
                        # Check request_variables first
                        if context and "request_variables" in context:
                            request_variables = context["request_variables"]
                            if variable_name in request_variables:
                                key = request_variables[variable_name]
                                logger.debug(f"Found context override for variable '{variable_name}'")

                        if key is None:
                            key = os.getenv(variable_name)
                            if key:
                                logger.info(
                                    f"Using environment variable {variable_name} for table column {column_name}"
                                )
                            else:
                                logger.error(f"Environment variable {variable_name} is not set.")
                    else:
                        # Load from database
                        key = await custom_component.get_variable(
                            name=variable_name, field=f"{table_field_name}.{column_name}", session=session
                        )

                except ValueError as e:
                    if "User id is not set" in str(e):
                        raise
                    logger.debug(str(e))
                    key = None

                # If we couldn't get from database and fallback is enabled, try environment
                if fallback_to_env_vars and key is None:
                    key = os.getenv(variable_name)
                    if key:
                        logger.info(f"Using environment variable {variable_name} for table column {column_name}")
                    else:
                        logger.error(f"Environment variable {variable_name} is not set.")

                # Update the column value with the resolved value
                updated_row[column_name] = key if key is not None else None
                if key is None:
                    logger.warning(
                        f"Could not get value for {variable_name} in table column {column_name}. Setting it to None."
                    )

            updated_table_data.append(updated_row)

        params[table_field_name] = updated_table_data
        return params