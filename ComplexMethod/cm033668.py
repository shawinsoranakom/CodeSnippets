def content_plugins() -> dict[str, dict[str, PluginInfo]]:
    """
    Analyze content.
    The primary purpose of this analysis is to facilitate mapping of integration tests to the plugin(s) they are intended to test.
    """
    plugins: dict[str, dict[str, PluginInfo]] = {}

    for plugin_type, plugin_directory in data_context().content.plugin_paths.items():
        plugin_paths = sorted(data_context().content.walk_files(plugin_directory))
        plugin_directory_offset = len(plugin_directory.split(os.path.sep))

        plugin_files: dict[str, list[str]] = {}

        for plugin_path in plugin_paths:
            plugin_filename = os.path.basename(plugin_path)
            plugin_parts = plugin_path.split(os.path.sep)[plugin_directory_offset:-1]

            if plugin_filename == '__init__.py':
                if plugin_type != 'module_utils':
                    continue
            else:
                plugin_name = os.path.splitext(plugin_filename)[0]

                if data_context().content.is_ansible and plugin_type == 'modules':
                    plugin_name = plugin_name.lstrip('_')

                plugin_parts.append(plugin_name)

            plugin_name = '.'.join(plugin_parts)

            plugin_files.setdefault(plugin_name, []).append(plugin_filename)

        plugins[plugin_type] = {plugin_name: PluginInfo(
            plugin_type=plugin_type,
            name=plugin_name,
            paths=paths,
        ) for plugin_name, paths in plugin_files.items()}

    return plugins