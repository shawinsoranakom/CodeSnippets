def get_vars_from_path(loader, path, entities, stage):
    data = {}
    if vars_loader._paths is None:
        # cache has been reset, reload all()
        _prime_vars_loader()

    for plugin_name in vars_loader._plugin_instance_cache:
        if (plugin := vars_loader.get(plugin_name)) is None:
            continue

        collection = '.' in plugin.ansible_name and not plugin.ansible_name.startswith('ansible.builtin.')
        # Warn if a collection plugin has REQUIRES_ENABLED because it has no effect.
        if collection and hasattr(plugin, 'REQUIRES_ENABLED'):
            display.warning(
                "Vars plugins in collections must be enabled to be loaded, REQUIRES_ENABLED is not supported. "
                "This should be removed from the plugin %s." % plugin.ansible_name
            )

        if not _plugin_should_run(plugin, stage):
            continue

        if (new_vars := plugin.get_vars(loader, path, entities)) != {}:
            data = combine_vars(data, new_vars)

    return data