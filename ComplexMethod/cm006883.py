def _find_config_file(override: Path | None) -> Path | None:
    """Return the first existing config file following the lookup order.

    Parameters
    ----------
    override:
        Explicit path supplied by the caller (``--environments-file``).
        If given, only this path is checked.

    Raises:
    ------
    ConfigError:
        If *override* is given but the file does not exist.
    """
    if override is not None:
        if not override.is_file():
            msg = f"Config file not found: {override}"
            raise ConfigError(msg)
        return override

    # Walk up from cwd looking for .lfx/environments.yaml
    cwd = Path.cwd()
    for directory in (cwd, *cwd.parents):
        for name in _YAML_NAMES:
            candidate = directory / _LFX_DIR / name
            if candidate.is_file():
                return candidate
        # Stop walking at a git root or the filesystem root
        if (directory / ".git").is_dir() or directory.parent == directory:
            break

    # User-level YAML
    for name in _YAML_NAMES:
        user_yaml = Path.home() / _LFX_DIR / name
        if user_yaml.is_file():
            return user_yaml

    # Backward-compat: langflow-environments.toml in cwd
    toml_fallback = cwd / _TOML_FALLBACK
    if toml_fallback.is_file():
        return toml_fallback

    return None