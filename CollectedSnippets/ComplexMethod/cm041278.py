def config_env_vars(cfg: ContainerConfiguration):
        """Sets all env vars from config.CONFIG_ENV_VARS."""

        profile_env = {}
        if config.LOADED_PROFILES:
            load_environment(profiles=",".join(config.LOADED_PROFILES), env=profile_env)

        non_prefixed_env_vars = []
        for env_var in config.CONFIG_ENV_VARS:
            value = os.environ.get(env_var, None)
            if value is not None:
                if (
                    env_var != "CI"
                    and not env_var.startswith("LOCALSTACK_")
                    and env_var not in profile_env
                ):
                    # Collect all env vars that are directly forwarded from the system env
                    # to the container which has not been prefixed with LOCALSTACK_ here.
                    # Suppress the "CI" env var.
                    # Suppress if the env var was set from the profile.
                    non_prefixed_env_vars.append(env_var)
                cfg.env_vars[env_var] = value

        # collectively log deprecation warnings for non-prefixed sys env vars
        if non_prefixed_env_vars:
            from localstack.utils.analytics import log

            for non_prefixed_env_var in non_prefixed_env_vars:
                # Show a deprecation warning for each individual env var collected above
                LOG.warning(
                    "Non-prefixed environment variable %(env_var)s is forwarded to the LocalStack container! "
                    "Please use `LOCALSTACK_%(env_var)s` instead of %(env_var)s to explicitly mark this environment variable to be forwarded from the CLI to the LocalStack Runtime.",
                    {"env_var": non_prefixed_env_var},
                )

            log.event(
                event="non_prefixed_cli_env_vars", payload={"env_vars": non_prefixed_env_vars}
            )