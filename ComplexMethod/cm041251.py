def _publish_config_as_analytics_event():
    env_vars = list(TRACKED_ENV_VAR)

    for key, value in os.environ.items():
        if key.startswith("PROVIDER_OVERRIDE_"):
            env_vars.append(key)
        elif key.startswith("SYNCHRONOUS_") and key.endswith("_EVENTS"):
            # these config variables have been removed with 3.0.0
            env_vars.append(key)

    env_vars = {key: os.getenv(key) for key in env_vars}
    present_env_vars = {env_var: 1 for env_var in PRESENCE_ENV_VAR if os.getenv(env_var)}

    # filter out irrelevant None values, making the payload significantly smaller.
    env_vars = {k: v for k, v in env_vars.items() if v is not None}
    present_env_vars = {k: v for k, v in present_env_vars.items() if v is not None}

    log.event("config", env_vars=env_vars, set_vars=present_env_vars)