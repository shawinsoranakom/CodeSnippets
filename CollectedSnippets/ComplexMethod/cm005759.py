def get_environment(
    name: str | None = None,
    *,
    config_file: Path | str | None = None,
) -> EnvironmentConfig:
    """Look up a named environment from the config file.

    If *name* is ``None``, the ``[defaults] environment`` key is used.

    Raises:
    ------
    EnvironmentNotFoundError
        If *name* is not defined in the config.
    EnvironmentConfigError
        If no default is set and *name* is ``None``.
    """
    # Find the config file once and reuse for both default lookup and environment loading.
    file_path: Path | None = None
    for candidate in _candidate_paths(config_file):
        if candidate.exists():
            file_path = candidate
            break

    if name is None:
        if file_path:
            raw = _load_toml(file_path)
            name = raw.get("defaults", {}).get("environment")
        if name is None:
            msg = "No environment name given and no [defaults] environment set in the config file."
            raise EnvironmentConfigError(msg)

    environments = load_environments(file_path or config_file)

    if name not in environments:
        raise EnvironmentNotFoundError(name)
    return environments[name]