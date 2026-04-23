def get_api_key_for_provider(user_id: UUID | str | None, provider: str, api_key: str | None = None) -> str | None:
    """Get API key from component input or global variables.

    When api_key is set to an environment variable name (e.g. ANTHROPIC_API_KEY),
    that name is resolved from os.environ or global variables so imported flows
    can reference credentials without storing the raw key.
    """

    # Resolve variable name (canonical or custom e.g. MY_OPENAI_API_KEY) from env or global vars
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

    if api_key and api_key.strip():
        var_name = api_key.strip()
        # Names that look like env/global variables (e.g. MY_OPENAI_API_KEY): resolve from env/DB
        if var_name.replace("_", "").isalnum() and var_name[0].isalpha():
            resolved = _resolve_var_name(var_name)
            if resolved:
                return resolved
            # Unresolved variable name: don't use as literal key
            if re.match(r"^[A-Z][A-Z0-9_]*$", var_name):
                return None
        # Literal API key (e.g. sk-...)
        return var_name

    # If no user_id or user_id is the string "None", we can't look up global variables
    if user_id is None or (isinstance(user_id, str) and user_id == "None"):
        return None

    # Get primary variable (first required secret) from provider metadata
    provider_variable_map = get_model_provider_variable_mapping()
    variable_name = provider_variable_map.get(provider)
    if not variable_name:
        return None

    # Try to get from global variables, fall back to environment
    async def _get_variable():
        async with session_scope() as session:
            variable_service = get_variable_service()
            if variable_service is None:
                return None
            try:
                return await variable_service.get_variable(
                    user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
                    name=variable_name,
                    field="",
                    session=session,
                )
            except ValueError:
                return None

    try:
        api_key = run_until_complete(_get_variable())
    except (ValueError, Exception):  # noqa: BLE001
        api_key = None

    if api_key:
        return api_key

    return os.getenv(variable_name)