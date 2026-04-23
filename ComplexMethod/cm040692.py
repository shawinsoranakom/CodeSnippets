def populate_config_env_var_names():
    global CONFIG_ENV_VARS

    CONFIG_ENV_VARS += [
        key
        for key in [key.upper() for key in os.environ]
        if (key.startswith("LOCALSTACK_") or key.startswith("PROVIDER_OVERRIDE_"))
        # explicitly exclude LOCALSTACK_CLI (it's prefixed with "LOCALSTACK_",
        # but is only used in the CLI (should not be forwarded to the container)
        and key != "LOCALSTACK_CLI"
    ]

    # create variable aliases prefixed with LOCALSTACK_ (except LOCALSTACK_HOST)
    CONFIG_ENV_VARS += [
        "LOCALSTACK_" + v for v in CONFIG_ENV_VARS if not v.startswith("LOCALSTACK_")
    ]

    CONFIG_ENV_VARS = list(set(CONFIG_ENV_VARS))