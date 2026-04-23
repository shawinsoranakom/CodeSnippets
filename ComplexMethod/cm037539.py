def load_plugins_by_group(group: str) -> dict[str, Callable[[], Any]]:
    """Load plugins registered under the given entry point group."""
    from importlib.metadata import entry_points

    allowed_plugins = envs.VLLM_PLUGINS

    discovered_plugins = entry_points(group=group)
    if len(discovered_plugins) == 0:
        logger.debug("No plugins for group %s found.", group)
        return {}

    # Check if the only discovered plugin is the default one
    is_default_group = group == DEFAULT_PLUGINS_GROUP
    # Use INFO for non-default groups and DEBUG for the default group
    log_level = logger.debug if is_default_group else logger.info

    log_level("Available plugins for group %s:", group)
    for plugin in discovered_plugins:
        log_level("- %s -> %s", plugin.name, plugin.value)

    if allowed_plugins is None:
        log_level(
            "All plugins in this group will be loaded. "
            "Set `VLLM_PLUGINS` to control which plugins to load."
        )

    plugins = dict[str, Callable[[], Any]]()
    for plugin in discovered_plugins:
        if allowed_plugins is None or plugin.name in allowed_plugins:
            if allowed_plugins is not None:
                log_level("Loading plugin %s", plugin.name)

            try:
                func = plugin.load()
                plugins[plugin.name] = func
            except Exception:
                logger.exception("Failed to load plugin %s", plugin.name)

    return plugins