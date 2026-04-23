def get_env_vars_to_copy(
    exclude_vars: set[str] | None = None,
    additional_vars: set[str] | None = None,
    destination: str | None = None,
) -> set[str]:
    """Return the env var names to copy from the driver to Ray actors.

    The result is the union of:

    1. Env vars registered in ``vllm.envs.environment_variables``.
    2. Env vars in ``os.environ`` matching a prefix in
       ``DEFAULT_ENV_VAR_PREFIXES`` + ``VLLM_RAY_EXTRA_ENV_VAR_PREFIXES_TO_COPY``.
    3. Individual names in ``DEFAULT_EXTRA_ENV_VARS`` +
       ``VLLM_RAY_EXTRA_ENV_VARS_TO_COPY``.
    4. Caller-supplied *additional_vars* (e.g. platform-specific).

    Minus any names in *exclude_vars* or ``RAY_NON_CARRY_OVER_ENV_VARS``.

    Args:
        exclude_vars: Env vars to exclude (e.g. worker-specific ones).
        additional_vars: Extra individual env var names to copy.  Useful
            for caller-specific vars (e.g. platform env vars).
        destination: Label used in log messages only.
    """
    exclude = (exclude_vars or set()) | RAY_NON_CARRY_OVER_ENV_VARS

    # -- prefixes (built-in + user-supplied, additive) ----------------------
    prefixes = DEFAULT_ENV_VAR_PREFIXES | _parse_csv(
        envs.VLLM_RAY_EXTRA_ENV_VAR_PREFIXES_TO_COPY
    )

    # -- collect env var names ----------------------------------------------
    # 1. vLLM's registered env vars
    result = set(envs.environment_variables)
    # 2. Prefix-matched vars present in the current environment
    result |= {name for name in os.environ if any(name.startswith(p) for p in prefixes)}
    # 3. Individual extra vars (built-in + user-supplied, additive)
    result |= DEFAULT_EXTRA_ENV_VARS | _parse_csv(envs.VLLM_RAY_EXTRA_ENV_VARS_TO_COPY)
    # 4. Caller-supplied extra vars (e.g. platform-specific)
    result |= additional_vars or set()
    # 5. Exclude worker-specific and user-blacklisted vars
    result -= exclude

    # -- logging ------------------------------------------------------------
    dest = f" to {destination}" if destination else ""
    logger.info("Env var prefixes to copy: %s", sorted(prefixes))
    logger.info(
        "Copying the following environment variables%s: %s",
        dest,
        sorted(v for v in result if v in os.environ),
    )
    if RAY_NON_CARRY_OVER_ENV_VARS:
        logger.info(
            "RAY_NON_CARRY_OVER_ENV_VARS from config: %s",
            RAY_NON_CARRY_OVER_ENV_VARS,
        )
    logger.info(
        "To exclude env vars from copying, add them to %s",
        RAY_NON_CARRY_OVER_ENV_VARS_FILE,
    )

    return result