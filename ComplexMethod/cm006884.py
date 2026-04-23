def resolve_environment(
    env: str | None,
    *,
    target: str | None = None,
    api_key: str | None = None,
    environments_file: str | None = None,
) -> LangflowEnvironment:
    """Resolve an environment name (or inline flags) to a :class:`LangflowEnvironment`.

    Precedence
    ----------
    1. **Inline mode** — if *target* is given, return immediately without
       reading any config file.  *api_key* is used as-is (its value, not a
       variable name).
    2. **Named env** — look up *env* (or the configured default) in the config
       file discovered by the lookup order described in this module's docstring.
    3. **Env-var fallback** — if no config file exists and no *env* was
       requested, fall back to ``LANGFLOW_URL`` / ``LANGFLOW_API_KEY`` (or
       ``LFX_URL`` / ``LFX_API_KEY``) env vars before raising.

    Parameters
    ----------
    env:
        Environment name from the config file (e.g. ``"staging"``).
    target:
        Inline URL override — bypasses config file lookup entirely.
    api_key:
        Inline API key value.  When used with *target*, taken as-is.
        When used alongside an *env* from the config, overrides the resolved key.
    environments_file:
        Explicit path to a config file (YAML or TOML).  Overrides the
        automatic discovery order.

    Returns:
    -------
    LangflowEnvironment:
        Fully-resolved environment with ``url`` and ``api_key``.

    Raises:
    ------
    ConfigError:
        When resolution fails: file not found, unknown environment name,
        malformed config, etc.
    """
    # -----------------------------------------------------------------------
    # Mode 1: inline (--target provided)
    # -----------------------------------------------------------------------
    if target is not None:
        name = env or "__inline__"
        return LangflowEnvironment(name=name, url=target, api_key=api_key)

    # -----------------------------------------------------------------------
    # Mode 2: config file
    # -----------------------------------------------------------------------
    override = Path(environments_file) if environments_file else None
    config_path = _find_config_file(override)

    if config_path is None:
        # No config file found — try env-var fallback before giving up
        lf_url = os.environ.get("LANGFLOW_URL") or os.environ.get("LFX_URL")
        if lf_url and env is None:
            lf_key = api_key or os.environ.get("LANGFLOW_API_KEY") or os.environ.get("LFX_API_KEY")
            return LangflowEnvironment(name="__env__", url=lf_url, api_key=lf_key)

        if env is not None:
            msg = (
                f"Environment {env!r} requested but no config file was found.\n"
                f"  • Create .lfx/environments.yaml in your project root, or\n"
                f"  • Pass --target <url> [--api-key <key>] for inline configuration.\n"
                f"  • Run 'lfx init' to scaffold a project with a config template."
            )
            raise ConfigError(msg)

        msg = (
            "No --env, --target URL, or config file found.\n"
            "Options:\n"
            "  • lfx <cmd> --env <name>              (requires .lfx/environments.yaml)\n"
            "  • lfx <cmd> --target <url>             (inline, no config file needed)\n"
            "  • export LANGFLOW_URL=<url>            (env-var fallback)\n"
            "  • lfx init                             (scaffold a project with a template)"
        )
        raise ConfigError(msg)

    all_envs, default_name = _load_config(config_path)

    resolved_name = env or default_name
    if resolved_name is None:
        available = ", ".join(sorted(all_envs)) or "(none defined)"
        msg = (
            f"No --env given and no 'defaults.environment' set in {config_path}.\n"
            f"Available environments: {available}\n"
            f"Pass --env <name> or add a 'defaults.environment' key to the config."
        )
        raise ConfigError(msg)

    if resolved_name not in all_envs:
        available = ", ".join(sorted(all_envs)) or "(none defined)"
        msg = f"Environment {resolved_name!r} not found in {config_path}.\nAvailable environments: {available}"
        raise ConfigError(msg)

    resolved = all_envs[resolved_name]

    # --api-key overrides the key resolved from the config file
    if api_key is not None:
        resolved = LangflowEnvironment(name=resolved.name, url=resolved.url, api_key=api_key)

    return resolved