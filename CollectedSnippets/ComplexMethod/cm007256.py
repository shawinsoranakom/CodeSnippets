def load_from_env_vars(params, load_from_db_fields, context=None):
    for field in load_from_db_fields:
        if field not in params or not params[field]:
            continue
        variable_name = params[field]
        key = None

        # Check request_variables in context
        if context and "request_variables" in context:
            request_variables = context["request_variables"]
            if variable_name in request_variables:
                key = request_variables[variable_name]
                logger.debug(f"Found context override for variable '{variable_name}'")

        if key is None:
            key = os.getenv(variable_name)
            if key:
                logger.info(f"Using environment variable {variable_name} for {field}")
            else:
                logger.error(f"Environment variable {variable_name} is not set.")
        params[field] = key if key is not None else None
        if key is None:
            logger.warning(f"Could not get value for {field}. Setting it to None.")
    return params