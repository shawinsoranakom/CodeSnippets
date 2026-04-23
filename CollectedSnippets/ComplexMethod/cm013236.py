def def_flag(
        name,
        env_var=None,
        default=False,
        include_in_repro=True,
        enabled_fn=lambda env_var_val, default: (
            (env_var_val != "0") if default else (env_var_val == "1")),
        implied_by_fn=lambda: False,
    ):
        enabled = default
        env_var_val = None
        if env_var is not None:
            env_var_val = os.getenv(env_var)
            enabled = enabled_fn(env_var_val, default)
        implied = implied_by_fn()
        enabled = enabled or implied
        if include_in_repro and (env_var is not None) and (enabled != default) and not implied:
            TestEnvironment.repro_env_vars[env_var] = env_var_val

        # export flag globally for convenience
        if name in globals():
            raise AssertionError(f"duplicate definition of flag '{name}'")
        globals()[name] = enabled
        return enabled